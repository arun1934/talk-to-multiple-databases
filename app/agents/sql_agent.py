from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta

import os
import litellm
import json
import redis
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging
import time
from functools import wraps
from decimal import Decimal
import re

# Import config
from app.config import get_config, REDIS, LLM, CACHE, DATABASE

logger = logging.getLogger(__name__)


def json_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


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
        # Configure LiteLLM directly
        litellm.api_key = LLM["api_key"]
        litellm.api_base = LLM["api_base"]

        # Set custom headers if provided
        if LLM["auth_header"]:
            litellm.headers = {"Authorization": LLM["auth_header"]}

        # Store model name and temperature for later use
        self.model = LLM["model"]
        self.generation_temperature = LLM["generation_temperature"]

        # Replace Trino with SQLAlchemy for Postgres
        self.db_url = DATABASE["nps_url"]

        # Create SQLAlchemy engine
        self.engine = create_engine(
            self.db_url,
            pool_size=DATABASE["pool_size"],
            max_overflow=DATABASE["max_overflow"],
            pool_timeout=DATABASE["pool_timeout"],
            pool_recycle=DATABASE["pool_recycle"]
        )

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

        # Configure Redis from config
        self.redis_client = redis.Redis(
            host=REDIS["host"],
            port=REDIS["port"],
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )

        self.schema_cache_key = "db_schema"
        self.query_cache_ttl = CACHE["query_cache_ttl"]
        self.schema_cache_ttl = CACHE["schema_cache_ttl"]

    def _create_db_connection(self):
        """Create a connection to Postgres"""
        try:
            return self.engine.connect()
        except Exception as e:
            logger.error(f"Failed to connect to Postgres: {str(e)}")
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
                "nps_db": {}
            }

            # Use SQLAlchemy inspector to get schema
            inspector = inspect(self.engine)

            # Get table columns for relevant tables
            for table_name in ['hyb_nps_dtl', 'dm_empmast', 'hyb_order_detail', 'hyb_product_data']:
                columns = []
                for column in inspector.get_columns(table_name, schema='public'):
                    columns.append([
                        column['name'],
                        str(column['type']),
                        'YES' if not column.get('nullable', True) else 'NO'
                    ])
                schema_info["nps_db"][table_name] = columns

            # Cache the schema
            self.redis_client.setex(
                self.schema_cache_key,
                self.schema_cache_ttl,
                json.dumps(schema_info)
            )

            return schema_info

        except Exception as e:
            logger.error(f"Error getting schema info: {str(e)}")
            raise DatabaseConnectionError(f"Failed to get schema information: {str(e)}")

    def get_cached_query_result(self, query: str, session_id: str = None) -> Optional[Dict[str, Any]]:
        """Get cached query result with consistent key generation"""
        logger.info(f"🔍 Looking for cached result for query: {query[:50]}...")

        if not CACHE["enable_llm_cache"]:
            logger.info(f"⚠️ Cache lookup skipped: Caching is disabled in configuration")
            return None

        try:
            # Normalize query by removing whitespace and converting to lowercase
            normalized_query = " ".join(query.lower().split())

            # Use a simple hash function less prone to variation
            import hashlib
            query_hash = hashlib.md5(normalized_query.encode()).hexdigest()

            # Try to get result with session-specific key
            if session_id:
                session_key = f"sql_query:{session_id}:{query_hash}"
                logger.debug(f"Trying session-specific cache key: {session_key}")

                cached = self.redis_client.get(session_key)
                if cached:
                    logger.info(f"✅ CACHE HIT (session) - Retrieved cached result ({len(cached)} bytes)")
                    return json.loads(cached)

            # Also try with just the query hash (session-independent)
            global_key = f"sql_query:{query_hash}"
            logger.debug(f"Trying global cache key: {global_key}")

            cached = self.redis_client.get(global_key)
            if cached:
                logger.info(f"✅ CACHE HIT (global) - Retrieved cached result ({len(cached)} bytes)")
                return json.loads(cached)

            logger.info(f"❌ CACHE MISS - No cached result found")

            # Debug: List keys matching pattern
            matching_keys = self.redis_client.keys("sql_query:*")
            if matching_keys:
                logger.debug(f"Existing cache keys: {matching_keys[:5]}")

        except Exception as e:
            logger.warning(f"❌ Cache retrieval failed: {str(e)}")

        return None

    def cache_query_result(self, query: str, result: Dict[str, Any], session_id: str = None):
        """Cache query result"""
        if not CACHE["enable_llm_cache"]:
            return

        try:
            # Normalize query by removing whitespace and converting to lowercase
            normalized_query = " ".join(query.lower().split())

            # Use a simple hash function less prone to variation
            import hashlib
            query_hash = hashlib.md5(normalized_query.encode()).hexdigest()

            # Serialize result to JSON string, with special handling for complex types
            result_json = json.dumps(result, default=json_serialize)

            # Cache with session-specific key if session_id provided
            if session_id:
                session_key = f"sql_query:{session_id}:{query_hash}"
                logger.debug(f"Caching with session key: {session_key}")

                self.redis_client.setex(
                    session_key,
                    self.query_cache_ttl,
                    result_json
                )

            # Also cache with global key (session-independent)
            global_key = f"sql_query:{query_hash}"
            logger.debug(f"Caching with global key: {global_key}")

            self.redis_client.setex(
                global_key,
                self.query_cache_ttl,
                result_json
            )

            logger.info(f"✅ Successfully cached result (TTL: {self.query_cache_ttl}s)")
        except Exception as e:
            logger.warning(f"❌ Cache storage failed: {str(e)}")

    def clear_query_cache(self):
        """Clear all cached SQL queries"""
        try:
            pattern = "sql_query:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached SQL queries")
            return True
        except Exception as e:
            logger.error(f"Error clearing query cache: {str(e)}")
            return False

    @retry_with_exponential_backoff(retries=3)
    def execute_sql(self, sql_query: str, session_id: str = None) -> Dict[str, Any]:
        """Execute SQL query with retry logic and proper error handling"""
        start_time = time.time()

        try:
            # Check cache first
            cached_result = self.get_cached_query_result(sql_query, session_id)
            if cached_result:
                logger.info(f"Cache hit for query: {sql_query[:50]}...")
                return cached_result

            # Use SQLAlchemy connection
            with self.engine.connect() as conn:
                # Execute the query
                result = conn.execute(text(sql_query))

                # Convert RMKeyView to list to make it JSON serializable
                columns = list(result.keys())
                results = result.fetchall()

                # Convert to list of lists for consistency
                results_list = [list(row) for row in results]

                query_result = {
                    "success": True,
                    "columns": columns,
                    "results": results_list,
                    "row_count": len(results_list),
                    "execution_time": time.time() - start_time
                }

                # Cache the successful result
                self.cache_query_result(sql_query, query_result, session_id)

                return query_result

        except Exception as e:
            logger.error(f"SQL execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }


    # - p_siteid: Concept or Site ID where the order was made (VARCHAR). Search with 'like' operator

    @retry_with_exponential_backoff(retries=2)
    def translate_nl_to_sql(self, query: str, schema_info: Dict[str, Any], history: List[Dict[str, Any]] = None) -> str:
        try:
            logger.info(f"Translating query to SQL: {query[:100]}...")

            # Build context from history with explicit time references
            context = ""
            if history and len(history) > 0:
                context += "Previous conversation with temporal context:\n"
                recent_history = history[-5:] if len(history) >= 5 else history

                for i, conv in enumerate(recent_history):
                    user_query = conv['query']
                    context += f"User question {i + 1}: {user_query}\n"
                    context += f"System response {i + 1}: {conv.get('answer', '')[:200]}...\n\n"

            # This is a context block to help the LLM understand the schema and data types.
            context += f"""Current schema information for nps_db:
{json.dumps(schema_info, indent=2)}

User query: {query}
Conversation history (last 3 turns):
{json.dumps(history[-3:], indent=2) if history else 'No history yet'}

Instructions for SQL generation:
1. **Table Usage:**
   - Prioritize using `public.hyb_nps_dtl` for NPS-related queries (scores, categories, comments, dates, regions, countries).
   - Use `public.hyb_order_detail` for order-specific data (quantity, price, order status).
   - Use `public.dm_empmast` for employee-related data.
   - Use `public.hyb_product_data` for product master data (product category, brand, launch date).
   - Only join tables when necessary based on the query. Explicitly use schema prefix `public.` (e.g., `public.hyb_nps_dtl`).

2. **Column Usage & NPS Domain Knowledge:**
   - `p_rating` in `public.hyb_nps_dtl` is the raw 0-10 NPS score. This column might be stored as text, so **ALWAYS cast `p_rating` to INTEGER (e.g., `CAST(p_rating AS INTEGER)`) before any numerical comparison or arithmetic.** This is the **ONLY** source for determining Promoter/Passive/Detractor status.
   - **NPS Categories (Promoter/Passive/Detractor) are DERIVED from `CAST(p_rating AS INTEGER)` as follows:**
     - Promoters: `CAST(p_rating AS INTEGER) >= 9`
     - Passives: `CAST(p_rating AS INTEGER) >= 7 AND CAST(p_rating AS INTEGER) <= 8`
     - Detractors: `CAST(p_rating AS INTEGER) <= 6`
   - The column `p_category` in `public.hyb_nps_dtl` is a **feedback topic category** (e.g., 'Communication', 'Delivery'), NOT the NPS Promoter/Passive/Detractor category. **DO NOT use `p_category` to group by Promoter/Passive/Detractor.**
   - `p_comment` in `public.hyb_nps_dtl` contains customer feedback.
   - **For direct NPS Score Calculation (e.g., overall NPS, trend of NPS score):**
     - Use the formula: `ROUND(CAST( (SUM(CASE WHEN CAST(p_rating AS INTEGER) >= 9 THEN 1 ELSE 0 END) - SUM(CASE WHEN CAST(p_rating AS INTEGER) <= 6 THEN 1 ELSE 0 END)) * 100.0 AS NUMERIC) / NULLIF(COUNT(*), 0), 2)`
     - This directly uses `CAST(p_rating AS INTEGER)` to count Promoters and Detractors.

3. **SQL Dialect and Functions:**
   - Use PostgreSQL syntax ONLY.
   - For date operations, prefer `DATE_TRUNC`, `EXTRACT`, `TO_CHAR`, and interval arithmetic.
   - For rounding, ensure the expression is cast to `NUMERIC` (e.g., `ROUND(CAST(expression AS NUMERIC), 2)`).
   - For division, always use `NULLIF(denominator, 0)` to prevent division by zero errors. For example, `SUM(value) / NULLIF(COUNT(*), 0)`.
   - Ensure all column names referenced in the query exist in the schema. Prefer `nps_date` over `survey_date` and `p_rating` over `rating` if those are the correct names in `hyb_nps_dtl`.

4. **Query Structure and Safety:**
   - Always include a `LIMIT` clause, defaulting to 100 if not otherwise specified by the query context (e.g. "top 5" implies LIMIT 5).
   - Avoid overly complex joins if a simpler query can answer the question.
   - Do NOT use `SELECT *`. Select only the necessary columns.
   - Ensure correct table and column names: `nps_date` (not `survey_date`), `p_rating` (not `rating`) in `hyb_nps_dtl`.

5. **Data Formatting for Charting (VERY IMPORTANT):**
   - **For distributions of Promoter/Passive/Detractor categories (e.g., "NPS category distribution by region"):**
     - You **MUST** generate a temporary NPS category column using a CASE statement based on `CAST(p_rating AS INTEGER)`.
     - Then, group by the primary dimension (e.g., region) AND this derived NPS category.
     - **Example for "distribution of NPS categories by region" (LONG format):**
       ```sql
       SELECT
         region,
         CASE
           WHEN CAST(p_rating AS INTEGER) >= 9 THEN 'Promoter'
           WHEN CAST(p_rating AS INTEGER) <= 6 THEN 'Detractor'
           ELSE 'Passive'
         END AS nps_derived_category,
         COUNT(*) AS nps_count
       FROM
         public.hyb_nps_dtl
       GROUP BY
         region,
         nps_derived_category
       ```
     - This "long" format output (`main_dimension, nps_derived_category, value_column`) is essential for charting these distributions.
     - **DO NOT use the `p_category` (feedback topic) column from the table when the user asks for Promoter/Passive/Detractor distributions.** You must derive it from `CAST(p_rating AS INTEGER)`.

6. **Column Naming and Aliases:**
   - Use clear, descriptive aliases for calculated columns (e.g., `total_sales`, `average_rating`, `nps_score`, `nps_derived_category`, `nps_count`).

Question to convert to SQL: {query}

If this question seems unclear or lacks context, assume it's about NPS data in table public.hyb_nps_dtl and do your best to generate a relevant SQL query.

SQL Query:"""

            logger.debug(f"Sending prompt to LLM: {context[:500]}...")

            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": context}],
                temperature=self.generation_temperature
            )

            sql_query = response.choices[0].message.content.strip()

            logger.debug(f"Raw LLM response: {sql_query[:500]}...")

            # Clean the SQL query
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()

            # Remove semicolon at the end if present
            if sql_query.endswith(';'):
                sql_query = sql_query[:-1].strip()
            
            # Add LIMIT if not present and not a common table expression (CTE)
            if "limit" not in sql_query.lower() and not sql_query.lower().strip().startswith("with"):
                sql_query += " LIMIT 100"
            elif sql_query.lower().strip().startswith("with") and "limit" not in sql_query.lower().split(")")[-1]:
                 # For CTEs, add LIMIT to the final SELECT statement
                # This is a basic check and might need refinement for complex CTEs
                # Find the last closing parenthesis of the CTE part
                last_paren_index = sql_query.rfind(')')
                if last_paren_index != -1:
                    final_select_part = sql_query[last_paren_index+1:]
                    if "limit" not in final_select_part.lower():
                        sql_query += " LIMIT 100"
                else: # No closing parenthesis found, might be malformed or simple WITH
                    if "limit" not in sql_query.lower(): # Apply to end if no clear CTE structure for limit
                         sql_query += " LIMIT 100"

            # Validate that the SQL contains at least one required table
            sql_lower = sql_query.lower()
            table_references = [
                'public.hyb_nps_dtl',
                'public.dm_empmast',
                'public.hyb_order_detail',
                'public.hyb_product_data',
                'hyb_nps_dtl',
                'dm_empmast',
                'hyb_order_detail',
                'hyb_product_data'
            ]

            found_table = False
            for table in table_references:
                if table in sql_lower:
                    found_table = True
                    break

            if not found_table:
                logger.warning(f"Generated SQL has no valid table references: {sql_query}")
                # Emergency fallback - generate a simple query that will work
                return """SELECT COUNT(*) AS count FROM public.hyb_nps_dtl LIMIT 100"""
                
            # Post-process SQL to fix common PostgreSQL issues
            # 1. Fix ROUND function to use NUMERIC type
            if "round(" in sql_lower or "ROUND(" in sql_query:
                # Find ROUND expressions, check if they need fixing, and replace them
                round_pattern = re.compile(r'ROUND\s*\(\s*(.*?)\s*,\s*(\d+)\s*\)', re.IGNORECASE)
                
                def replace_round(match):
                    expr, digits = match.groups()
                    # If expression doesn't already have CAST to NUMERIC, add it
                    if "::numeric" not in expr.lower() and "as numeric" not in expr.lower():
                        return f"ROUND(CAST({expr} AS NUMERIC), {digits})"
                    return match.group(0)
                    
                sql_query = round_pattern.sub(replace_round, sql_query)
                
                # Also check for FLOAT casts and replace with NUMERIC
                sql_query = re.sub(r'::FLOAT', '::NUMERIC', sql_query, flags=re.IGNORECASE)
                sql_query = re.sub(r'AS FLOAT', 'AS NUMERIC', sql_query, flags=re.IGNORECASE)
            
            # 2. Check for divisions without NULLIF and fix them
            # Regex to find division a / b where b is not already NULLIF(b,0)
            # Handles potential casting like ::NUMERIC
            # Simplified to remove variable-width lookbehind, relying on replace_division logic.
            division_pattern = re.compile(r'([\w\.\(\)\[\]\*\-\+\s]+(?:\:\:NUMERIC)?)\s*\/\s*([\w\.\(\)\[\]\*\-\+\s]+(?:\:\:NUMERIC)?)', re.IGNORECASE)

            def replace_division(match):
                numerator = match.group(1).strip()
                denominator = match.group(2).strip()
                
                # Avoid double-wrapping if by some chance it was missed by lookbehind
                if denominator.lower().startswith("nullif"):
                    return f"{numerator} / {denominator}" # Already handled or complex
                return f"{numerator} / NULLIF({denominator}, 0)"
            
            # Iteratively apply division fix to handle multiple occurrences
            new_sql_query = sql_query
            while True:
                transformed_sql = division_pattern.sub(replace_division, new_sql_query)
                if transformed_sql == new_sql_query: # No more changes
                    break
                new_sql_query = transformed_sql
            sql_query = new_sql_query
            
            # 3. Check NPS calculation pattern and ensure it uses proper types and NULLIF
            # This is more specific for typical NPS formulas.
            if "nps" in sql_lower and ("promoters" in sql_lower or "detractors" in sql_lower):
                # Ensure ::NUMERIC for any float casts
                if "::float" in sql_lower:
                    sql_query = re.sub(r'::float', '::NUMERIC', sql_query, flags=re.IGNORECASE)
                
                # Ensure NULLIF for common NPS calculation patterns
                # Pattern: (SUM(...) - SUM(...)) * 100.0 / COUNT(...)
                # Or similar structures for percentage calculations.
                nps_percentage_pattern = re.compile(
                    r'(\(?\s*SUM\s*\(CASE WHEN.*?THEN 1 ELSE 0 END\)\s*-\s*SUM\s*\(CASE WHEN.*?THEN 1 ELSE 0 END\)\s*\)?\s*\*\s*100(?:\.0)?)\s*\/\s*(COUNT\s*\(\s*\*\s*\)|SUM\s*\(.*?\))'
                    , re.IGNORECASE | re.DOTALL
                )
                sql_query = nps_percentage_pattern.sub(
                    lambda m: f"{m.group(1)} / NULLIF({m.group(2)}, 0)",
                    sql_query
                )

            logger.info(f"Processed SQL query: {sql_query}")
            return sql_query

        except Exception as e:
            logger.error(f"Error translating NL to SQL: {str(e)}", exc_info=True)
            raise AIServiceError(f"Failed to translate natural language to SQL: {str(e)}")

    def process_query_with_memory(self, query: str, history: List[Dict[str, Any]], session_id: str = None) -> Dict[
        str, Any]:
        """Process a query using conversation history and schema information."""
        try:
            schema_info = self.get_schema_info()
            sql_query = self.translate_nl_to_sql(query, schema_info, history)
            results = self.execute_sql(sql_query, session_id=session_id)

            # Attempt to generate a natural language answer from the results
            nl_answer = self.translate_results_to_nl(query, sql_query, results)

            return {
                "success": True,
                "answer": nl_answer,
                "sql_query": sql_query,
                "results": results
            }

        except DatabaseConnectionError as db_err:
            logger.error(f"Database connection error: {db_err}")
            return {"success": False, "error": str(db_err)}
        except QueryExecutionError as q_err:
            logger.error(f"Query execution error: {q_err}")
            return {"success": False, "error": str(q_err)}
        except AIServiceError as ai_err:
            logger.error(f"AI service error: {ai_err}")
            return {"success": False, "error": str(ai_err)}
        except Exception as e:
            logger.error(f"Unexpected error processing query: {str(e)}", exc_info=True)
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def translate_results_to_nl(self, query: str, sql_query: str, results: Dict[str, Any]) -> str:
        """Translate SQL query results into a natural language answer."""
        try:
            if not results or not results.get("success"):
                return "I couldn't retrieve any data for your query."

            data_for_nl = {
                "columns": results.get("columns", []),
                "rows": results.get("results", [])[:5]  # Send first 5 rows for context
            }
            num_rows = len(results.get("results", []))

            prompt = f"""You are an AI assistant. Given a user's question, the SQL query used, and the results, provide a concise, natural language answer.

User Question: {query}
SQL Query: {sql_query}
Results (first 5 rows shown, total {num_rows} rows):
{json.dumps(data_for_nl, indent=2, default=json_serialize)}

Guidelines for the answer:
- Be direct and answer the question based on the results.
- If the results are empty (0 rows), explicitly state that no data was found matching the criteria.
- If there are many rows, summarize the findings rather than listing everything.
- For numerical results, present them clearly. If it's a single number, state it. If it's a list, summarize.
- For NPS data:
  - Interpret NPS scores: <0 is Needs Improvement, 0-30 is Good, 31-70 is Great, >70 is Excellent. Contextualize this.
  - When discussing NPS distribution (Promoters, Passives, Detractors), highlight key proportions.
  - If specific comments are queried, summarize themes if many, or list a few if few.
  - If trends are shown, describe the trend (e.g., "NPS increased from X to Y over the period.").
- Avoid simply re-stating the SQL query or column names unless necessary for clarity.
- Keep the answer concise and easy to understand. Do not be too verbose.
- If the query was for a KPI like "Total Promoters", the answer should be direct, e.g., "The total number of promoters is X."

Answer:"""

            logger.debug(f"Sending prompt to LLM for NL translation: {prompt[:500]}...")

            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=LLM["summary_temperature"]
            )
            nl_answer = response.choices[0].message.content.strip()
            logger.info(f"Generated NL answer: {nl_answer[:200]}...")
            return nl_answer

        except Exception as e:
            logger.error(f"Error translating results to NL: {str(e)}", exc_info=True)
            return "I found some data, but I had trouble summarizing it."