from typing import Dict, Any, List, Optional
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage
import trino
import json
import redis

class SQLAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0
        )
        self.trino_conn = self._create_trino_connection()
        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            decode_responses=True
        )
        self.schema_cache_key = "db_schema"
        
    def _create_trino_connection(self):
        """Create a connection to Trino"""
        return trino.dbapi.connect(
            host='trino',
            port=8080,
            user='trino',
            catalog=None  # We'll specify catalog in queries
        )
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information from both databases"""
        # Try to get from cache first
        cached_schema = self.redis_client.get(self.schema_cache_key)
        if cached_schema:
            try:
                return json.loads(cached_schema)
            except json.JSONDecodeError:
                pass
        
        schema_info = {
            "nps_db": {},
            "products_db": {}
        }
        
        cursor = self.trino_conn.cursor()
        
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
        
        # Cache the schema
        self.redis_client.setex(
            self.schema_cache_key,
            3600,  # Cache for 1 hour
            json.dumps(schema_info)
        )
        
        return schema_info
    
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query via Trino"""
        try:
            cursor = self.trino_conn.cursor()
            cursor.execute(sql_query)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = cursor.fetchall()
            
            return {
                "success": True,
                "columns": columns,
                "results": results,
                "row_count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def translate_nl_to_sql(self, query: str, schema_info: Dict[str, Any]) -> str:
        """Translate natural language to SQL using LLM"""
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
8. DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database."""),
            HumanMessage(content=query)
        ])
        
        # Format the prompt before sending
        formatted_prompt = prompt.format_messages()
        response = self.llm.invoke(formatted_prompt)
        
        # Clean the SQL query - remove markdown formatting
        sql_query = response.content.strip()
        
        # Remove markdown code blocks if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        elif sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()
        
        return sql_query
    
    def translate_results_to_nl(self, query: str, sql_query: str, results: Dict[str, Any]) -> str:
        """Translate SQL results back to natural language"""
        if not results["success"]:
            return f"I encountered an error executing the query: {results['error']}"
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Convert SQL query results to a natural language response.
Be conversational and helpful. If the results are empty, say so clearly.
For numerical results, provide appropriate context and insights."""),
            HumanMessage(content=f"""
Original question: {query}
SQL query: {sql_query}
Results: {json.dumps(results, default=str)}

Please provide a natural language response to the original question.""")
        ])
        
        # Format the prompt before sending
        formatted_prompt = prompt.format_messages()
        response = self.llm.invoke(formatted_prompt)
        return response.content.strip()
    
    def process_query_with_memory(self, query: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process query with conversation history context"""
        # Get schema information
        schema_info = self.get_schema_info()
        
        # Build context from history
        context = ""
        if history:
            recent_history = history[-3:]  # Last 3 conversations
            for conv in recent_history:
                context += f"User: {conv['query']}\nSQL: {conv['sql_query']}\n\n"
        
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
            "needs_correction": False
        }
