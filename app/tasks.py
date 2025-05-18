from celery import Celery, Task
from datetime import datetime, date
import os
from typing import Dict, Any, List
import redis
import json
import logging
import time
from decimal import Decimal
from prometheus_client import Counter, Histogram
from .agents.sql_agent import SQLAgent, DatabaseConnectionError, AIServiceError
from .graphs.correction_graph import create_correction_graph

# Import config
from app.config import CELERY, REDIS, CACHE

# Configure logging
logger = logging.getLogger(__name__)

# Metrics
task_counter = Counter('celery_tasks_total', 'Total Celery tasks', ['task_name', 'status'])
task_duration = Histogram('celery_task_duration_seconds', 'Celery task duration', ['task_name'])

# Initialize Celery
celery_app = Celery(
    "sql_chat_agent",
    broker=CELERY["broker_url"],
    backend=CELERY["result_backend"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=CELERY["task_time_limit"],
    task_soft_time_limit=CELERY["task_soft_time_limit"],
    worker_prefetch_multiplier=CELERY["worker_prefetch_multiplier"],
    worker_max_tasks_per_child=CELERY["worker_max_tasks_per_child"],
    task_acks_late=True,
    worker_max_memory_per_child=CELERY["worker_max_memory_per_child"],
    broker_connection_retry_on_startup=True,
)

# Define the json_serialize function at the top of tasks.py as well
def json_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

class LogErrorsTask(Task):
    """Custom task class that logs errors"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {self.name} [{task_id}] failed: {exc}", exc_info=True)
        task_counter.labels(task_name=self.name, status='failed').inc()

    def on_success(self, retval, task_id, args, kwargs):
        task_counter.labels(task_name=self.name, status='success').inc()

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task {self.name} [{task_id}] retrying: {exc}")
        task_counter.labels(task_name=self.name, status='retry').inc()


@celery_app.task(
    name="process_query_task",
    bind=True,
    base=LogErrorsTask,
    max_retries=3,
    default_retry_delay=5
)
def process_query_task(self, query: str, session_id: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a natural language query asynchronously with comprehensive error handling"""
    start_time = time.time()

    try:
        # Import here to avoid circular imports
        from .agents.sql_agent import SQLAgent, DatabaseConnectionError, AIServiceError
        from .graphs.correction_graph import create_correction_graph

        # Initialize SQL agent
        sql_agent = SQLAgent()

        # Process query with memory context
        logger.info(f"Processing query for session {session_id}: {query[:50]}...")

        result = sql_agent.process_query_with_memory(query, history, session_id)  # Pass session_id here

        # Check if SQL generation failed
        if not result.get("sql_query"):
            logger.warning(f"SQL generation failed for query: {query[:50]}")
            result["execution_time"] = time.time() - start_time
            return result

        # Run correction graph if needed
        if result.get("needs_correction", False):
            logger.info(f"Running correction graph for query: {query[:50]}...")

            correction_graph = create_correction_graph()

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
                execution_result = sql_agent.execute_sql(corrected_sql, session_id)  # Pass session_id here

                if execution_result["success"]:
                    # Translate results to natural language
                    answer = sql_agent.translate_results_to_nl(query, corrected_sql, execution_result)
                    result = {
                        "success": True,
                        "answer": answer,
                        "sql_query": corrected_sql,
                        "results": execution_result,
                        "needs_correction": False,
                        "was_corrected": True
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

        # Add execution time
        result["execution_time"] = time.time() - start_time

        # Cache the result if caching is enabled
        # Cache the result if caching is enabled
        if CACHE["enable_llm_cache"]:
            try:
                # Normalize query by removing whitespace and converting to lowercase
                normalized_query = " ".join(query.lower().split())

                # Use a simple hash function less prone to variation
                import hashlib
                query_hash = hashlib.md5(normalized_query.encode()).hexdigest()

                cache_key = f"query_result:{session_id}:{query_hash}"
                redis_client = redis.Redis.from_url(REDIS["url"])
                redis_client.setex(
                    cache_key,
                    CACHE["query_cache_ttl"],
                    json.dumps(result, default=json_serialize)
                )
                logger.info(f"Successfully cached query result")
            except Exception as e:
                logger.warning(f"Failed to cache query result: {str(e)}")
        # Record metrics
        task_duration.labels(task_name="process_query_task").observe(time.time() - start_time)

        return result

    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=5 * (self.request.retries + 1))
        return {"error": f"Database connection error: {str(e)}", "success": False}

    except AIServiceError as e:
        logger.error(f"AI service error: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=5 * (self.request.retries + 1))
        return {"error": f"AI service error: {str(e)}", "success": False}

    except Exception as e:
        logger.error(f"Unexpected error in process_query_task: {str(e)}", exc_info=True)
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=5 * (self.request.retries + 1))
        return {"error": str(e), "success": False}

@celery_app.task(
    name="generate_suggestions_task",
    base=LogErrorsTask,
    max_retries=2
)
def generate_suggestions_task(query: str, answer: str, history: List[Dict[str, Any]]) -> List[str]:
    """Generate follow-up suggestions asynchronously with error handling"""
    start_time = time.time()

    try:
        from .services.suggestion_service import SuggestionService

        suggestion_service = SuggestionService()
        suggestions = suggestion_service.generate_suggestions(query, answer, history)

        # Record metrics
        task_duration.labels(task_name="generate_suggestions_task").observe(time.time() - start_time)

        return suggestions

    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return []


@celery_app.task(
    name="cache_schema_task",
    base=LogErrorsTask
)
def cache_schema_task() -> bool:
    """Periodically cache database schema with error handling"""
    start_time = time.time()

    try:
        # Import here to avoid circular imports
        from .agents.sql_agent import SQLAgent

        sql_agent = SQLAgent()
        schema_info = sql_agent.get_schema_info()

        redis_client = redis.Redis.from_url(REDIS["url"])
        redis_client.set(
            "db_schema",
            json.dumps(schema_info),
            ex=CACHE["schema_cache_ttl"]
        )

        logger.info("Successfully cached database schema")

        # Record metrics
        task_duration.labels(task_name="cache_schema_task").observe(time.time() - start_time)

        return True

    except Exception as e:
        logger.error(f"Error caching schema: {str(e)}")
        return False


@celery_app.task(
    name="cleanup_sessions_task",
    base=LogErrorsTask
)
def cleanup_sessions_task() -> Dict[str, Any]:
    """Periodically clean up expired sessions"""
    start_time = time.time()

    try:
        from .services.memory_service import MemoryService

        memory_service = MemoryService()
        memory_service.cleanup_expired_sessions()

        # Record metrics
        task_duration.labels(task_name="cleanup_sessions_task").observe(time.time() - start_time)

        return {"status": "success", "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": datetime.utcnow().isoformat()}


# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'cache-schema-every-hour': {
        'task': 'cache_schema_task',
        'schedule': CACHE["schema_cache_ttl"],  # Use the schema cache TTL from config
    },
    'cleanup-sessions-every-6-hours': {
        'task': 'cleanup_sessions_task',
        'schedule': 21600.0,  # Run every 6 hours
    },
}


# Health check task
@celery_app.task(name="health_check_task")
def health_check_task():
    """Simple health check task"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}