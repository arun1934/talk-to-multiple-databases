from celery import Celery
import os
from typing import Dict, Any, List
import redis
import json
from datetime import datetime

# Initialize Celery
celery_app = Celery(
    "sql_chat_agent",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,  # 60 seconds timeout
    task_soft_time_limit=50,  # Soft timeout
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@celery_app.task(name="process_query_task", bind=True, max_retries=3)
def process_query_task(self, query: str, session_id: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a natural language query asynchronously
    """
    try:
        # Import here to avoid circular imports
        from .agents.sql_agent import SQLAgent
        from .graphs.correction_graph import create_correction_graph
        
        # Initialize SQL agent
        sql_agent = SQLAgent()
        
        # Create correction graph
        correction_graph = create_correction_graph()
        
        # Process query with memory context
        result = sql_agent.process_query_with_memory(query, history)
        
        # Run correction graph if needed
        if result.get("needs_correction", False):
            corrected_result = correction_graph.invoke({
                "query": query,
                "sql": result["sql_query"],
                "error": result.get("error"),
                "schema": sql_agent.get_schema_info(),
                "max_attempts": 3
            })
            
            # Check if correction was successful
            if corrected_result.get('final_result', {}).get('success', False):
                # Execute the corrected SQL
                corrected_sql = corrected_result['final_result']['sql_query']
                execution_result = sql_agent.execute_sql(corrected_sql)
                
                if execution_result["success"]:
                    # Translate results to natural language
                    answer = sql_agent.translate_results_to_nl(query, corrected_sql, execution_result)
                    result = {
                        "success": True,
                        "answer": answer,
                        "sql_query": corrected_sql,
                        "results": execution_result,
                        "needs_correction": False
                    }
                else:
                    result = {
                        "success": False,
                        "error": execution_result["error"],
                        "sql_query": corrected_sql,
                        "answer": f"I encountered an error: {execution_result['error']}"
                    }
            else:
                result = {
                    "success": False,
                    "error": corrected_result.get('final_result', {}).get('error', 'Failed to correct SQL'),
                    "sql_query": result["sql_query"],
                    "answer": "I'm having trouble understanding your query. Could you rephrase it?"
                }
        
        # Cache the result
        cache_key = f"query_result:{session_id}:{hash(query)}"
        redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        redis_client.setex(
            cache_key,
            300,  # Cache for 5 minutes
            json.dumps(result)
        )
        
        return result
        
    except Exception as e:
        # Log error and potentially retry
        self.retry(exc=e, countdown=5)
        return {"error": str(e)}

@celery_app.task(name="generate_suggestions_task")
def generate_suggestions_task(query: str, answer: str, history: List[Dict[str, Any]]) -> List[str]:
    """
    Generate follow-up suggestions asynchronously
    """
    try:
        from .services.suggestion_service import SuggestionService
        
        suggestion_service = SuggestionService()
        suggestions = suggestion_service.generate_suggestions(query, answer, history)
        
        return suggestions
        
    except Exception as e:
        return []

@celery_app.task(name="cache_schema_task")
def cache_schema_task() -> bool:
    """
    Periodically cache database schema
    """
    try:
        # Import here to avoid circular imports
        from .agents.sql_agent import SQLAgent
        
        sql_agent = SQLAgent()
        schema_info = sql_agent.get_schema_info()
        
        redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        redis_client.set(
            "db_schema",
            json.dumps(schema_info),
            ex=3600  # Cache for 1 hour
        )
        
        return True
        
    except Exception as e:
        return False

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'cache-schema-every-hour': {
        'task': 'cache_schema_task',
        'schedule': 3600.0,  # Run every hour
    },
}
