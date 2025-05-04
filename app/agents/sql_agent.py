from typing import Dict, Any, List, Optional
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import trino
import json
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
import time
from functools import wraps

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    pass


class QueryExecutionError(Exception):
    pass


class AIServiceError(Exception):
    pass


def retry_with_exponential_backoff(retries=3, base_delay=1, max_delay=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


class SQLAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0
        )

        # We'll use Trino connection directly instead of SQLAlchemy
        # since Trino doesn't work well with SQLAlchemy text execution
        self.trino_host = 'trino'
        self.trino_port = 8080
        self.trino_user = 'trino'

        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )

        self.schema_cache_key = "db_schema"
        self.query_cache_ttl = 300  # 5 minutes

    def _create_trino_connection(self):
        """Create a connection to Trino"""
        try:
            return trino.dbapi.connect(
                host=self.trino_host,
                port=self.trino_port,
                user=self.trino_user
            )
        except Exception as e:
            logger.error(f"Failed to connect to Trino: {str(e)}")
            raise DatabaseConnectionError(f"Cannot connect to database: {str(e)}")

    @retry_with_exponential_backoff(retries=3)
    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information with caching and retry logic"""
        try:
            # Try to get from cache first
            cached_schema = self.redis_client.get(self.schema_cache_key)
            if cached_schema:
                try:
                    return json.loads(cached_schema)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse cached schema")

            schema_info = {
                "nps_db": {},
                "products_db": {}
            }

            # Use trino connection instead of SQLAlchemy for schema queries
            conn = trino.dbapi.connect(
                host='trino',
                port=8080,
                user='trino'
            )
            cursor = conn.cursor()

            try:
                # Get NPS database schema
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM nps_db.information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'nps_feedback'
                """)
                schema_info["nps_db"]["nps_feedback"] = cursor.fetchall()

                # Get Products database schema
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM products_db.information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'products'
                """)
                schema_info["products_db"]["products"] = cursor.fetchall()
            finally:
                cursor.close()
                conn.close()

            # Cache the schema
            self.redis_client.setex(
                self.schema_cache_key,
                3600,  # Cache for 1 hour
                json.dumps(schema_info)
            )

            return schema_info

        except Exception as e:
            logger.error(f"Error getting schema info: {str(e)}")
            raise DatabaseConnectionError(f"Failed to get schema information: {str(e)}")

    def get_cached_query_result(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached query result if available"""
        try:
            cache_key = f"query_result:{hash(query)}"
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
        return None

    def cache_query_result(self, query: str, result: Dict[str, Any]):
        """Cache query result"""
        try:
            cache_key = f"query_result:{hash(query)}"
            self.redis_client.setex(cache_key, self.query_cache_ttl, json.dumps(result))
        except Exception as e:
            logger.warning(f"Cache storage failed: {str(e)}")

    @retry_with_exponential_backoff(retries=3)
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query with retry logic and proper error handling"""
        start_time = time.time()

        try:
            # Check cache first
            cached_result = self.get_cached_query_result(sql_query)
            if cached_result:
                logger.info(f"Cache hit for query: {sql_query[:50]}...")
                return cached_result

            # Use trino connection directly
            conn = trino.dbapi.connect(
                host='trino',
                port=8080,
                user='trino'
            )
            cursor = conn.cursor()

            try:
                cursor.execute(sql_query)

                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                results = cursor.fetchall()

                query_result = {
                    "success": True,
                    "columns": columns,
                    "results": results,
                    "row_count": len(results),
                    "execution_time": time.time() - start_time
                }

                # Cache the successful result
                self.cache_query_result(sql_query, query_result)

                return query_result
            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            logger.error(f"SQL execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    @retry_with_exponential_backoff(retries=2)
    def translate_nl_to_sql(self, query: str, schema_info: Dict[str, Any]) -> str:
        """Translate natural language to SQL with retry logic"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""You are a SQL expert. Convert natural language queries to Trino SQL.

Database Schema:
NPS Database (nps_db.public.nps_feedback):
- feedback_id: integer (primary key)
- product_id: integer (foreign key)
- rating: integer (1-5)
- comment: text
- category: varchar
- subcategory: varchar
- region: varchar
- carpenter_name: varchar
- driver_name: varchar
- created_at: timestamp

Products Database (products_db.public.products):
- product_id: integer (primary key)
- product_name: varchar
- description: text
- price: decimal
- sku: varchar
- created_at: timestamp

Rules:
1. Use fully qualified table names: nps_db.public.nps_feedback and products_db.public.products
2. Join on product_id when needed
3. Use appropriate aggregations for analytical queries
4. Include relevant filters based on the question
5. Use proper date functions for time-based queries
6. Return only the SQL query, no explanations
7. Do not include markdown formatting, just the raw SQL
8. DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
9. Always limit results to prevent overwhelming the system (default LIMIT 100 unless specified otherwise)
10. DO NOT use semicolons (;) at the end of the query - Trino does not require them"""),
                HumanMessage(content=query)
            ])

            formatted_prompt = prompt.format_messages()
            response = self.llm.invoke(formatted_prompt)

            sql_query = response.content.strip()

            # Clean the SQL query
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()

            # Remove semicolon at the end if present (Trino doesn't like them)
            if sql_query.endswith(';'):
                sql_query = sql_query[:-1].strip()

            # Add LIMIT if not present
            if "LIMIT" not in sql_query.upper():
                sql_query += " LIMIT 100"

            return sql_query

        except Exception as e:
            logger.error(f"Error translating NL to SQL: {str(e)}")
            raise AIServiceError(f"Failed to translate query: {str(e)}")

    @retry_with_exponential_backoff(retries=2)
    def translate_results_to_nl(self, query: str, sql_query: str, results: Dict[str, Any]) -> str:
        """Translate SQL results to natural language with retry logic"""
        try:
            if not results["success"]:
                return f"I encountered an error executing the query: {results['error']}"

            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""Convert SQL query results to a natural language response.
Be conversational and helpful. If the results are empty, say so clearly.
For numerical results, provide appropriate context and insights.
Keep the response concise but informative."""),
                HumanMessage(content=f"""
Original question: {query}
SQL query: {sql_query}
Results: {json.dumps(results, default=str)}

Please provide a natural language response to the original question.""")
            ])

            formatted_prompt = prompt.format_messages()
            response = self.llm.invoke(formatted_prompt)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error translating results to NL: {str(e)}")
            raise AIServiceError(f"Failed to translate results: {str(e)}")

    def process_query_with_memory(self, query: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process query with conversation history context and comprehensive error handling"""
        try:
            # Get schema information
            schema_info = self.get_schema_info()

            # Build context from history
            context = ""
            if history:
                recent_history = history[-3:]  # Last 3 conversations
                for conv in recent_history:
                    context += f"User: {conv['query']}\nSQL: {conv.get('sql_query', '')}\n\n"

            # Enhanced prompt with context
            enhanced_query = f"""
Previous context:
{context}

Current question: {query}
"""

            # Generate SQL
            sql_query = self.translate_nl_to_sql(enhanced_query, schema_info)

            # Execute SQL
            results = self.execute_sql(sql_query)

            # Check if we need correction
            if not results["success"]:
                return {
                    "needs_correction": True,
                    "sql_query": sql_query,
                    "error": results["error"],
                    "original_query": query
                }

            # Translate results to natural language
            answer = self.translate_results_to_nl(query, sql_query, results)

            return {
                "success": True,
                "answer": answer,
                "sql_query": sql_query,
                "results": results,
                "needs_correction": False,
                "execution_time": results.get("execution_time", 0)
            }

        except DatabaseConnectionError as e:
            logger.error(f"Database connection error: {str(e)}")
            return {
                "success": False,
                "error": f"Database connection error: {str(e)}",
                "needs_correction": False
            }
        except AIServiceError as e:
            logger.error(f"AI service error: {str(e)}")
            return {
                "success": False,
                "error": f"AI service error: {str(e)}",
                "needs_correction": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in process_query_with_memory: {str(e)}")
            return {
                "success": False,
                "error": f"An unexpected error occurred: {str(e)}",
                "needs_correction": False
            }