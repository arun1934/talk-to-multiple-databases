from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import json
import logging
import time
import re
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import psutil

from .services.memory_service import MemoryService
from .services.suggestion_service import SuggestionService
from .tasks import process_query_task
from .agents.sql_agent import SQLAgent, DatabaseConnectionError, QueryExecutionError, AIServiceError
from .graphs.correction_graph import create_correction_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define metrics
query_counter = Counter('sql_queries_total', 'Total SQL queries executed')
query_latency = Histogram('sql_query_duration_seconds', 'SQL query duration')
active_sessions = Gauge('active_sessions', 'Number of active sessions')
error_counter = Counter('application_errors_total', 'Total application errors', ['error_type'])
cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')

app = FastAPI(
    title="SQL Chat Agent",
    description="Natural language interface for SQL databases",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration
from collections import defaultdict
import asyncio


class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.cleanup_interval = 60
        self.last_cleanup = time.time()

    async def check_rate_limit(self, client_ip: str) -> bool:
        now = time.time()

        # Cleanup old requests periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
            self.last_cleanup = now

        # Clean old requests for this client
        self.requests[client_ip] = [req_time for req_time in self.requests[client_ip]
                                    if now - req_time < 60]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False

        self.requests[client_ip].append(now)
        return True

    def _cleanup(self):
        """Clean up old request records"""
        now = time.time()
        for ip in list(self.requests.keys()):
            self.requests[ip] = [req_time for req_time in self.requests[ip]
                                 if now - req_time < 60]
            if not self.requests[ip]:
                del self.requests[ip]


rate_limiter = RateLimiter(requests_per_minute=30)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
memory_service = MemoryService()
suggestion_service = SuggestionService()
sql_agent = SQLAgent()


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        if len(v) > 1000:
            raise ValueError('Query too long (max 1000 characters)')
        if re.search(r'(DROP|DELETE|TRUNCATE|ALTER)\s+TABLE', v, re.IGNORECASE):
            raise ValueError('DDL operations not allowed')
        return v.strip()


class QueryResponse(BaseModel):
    answer: str
    sql_query: str
    suggestions: List[str]
    session_id: str
    execution_time: Optional[float] = None


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error_counter.labels(error_type=type(exc).__name__).inc()

    if isinstance(exc, DatabaseConnectionError):
        return JSONResponse(
            status_code=503,
            content={"error": "Database connection error", "detail": str(exc)}
        )
    elif isinstance(exc, QueryExecutionError):
        return JSONResponse(
            status_code=400,
            content={"error": "Query execution error", "detail": str(exc)}
        )
    elif isinstance(exc, AIServiceError):
        return JSONResponse(
            status_code=503,
            content={"error": "AI service error", "detail": str(exc)}
        )
    elif isinstance(exc, HTTPException):
        raise exc  # Let FastAPI handle it
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": "An unexpected error occurred"}
        )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to add process time header and handle rate limiting"""
    start_time = time.time()
    client_ip = request.client.host

    # Check rate limit
    if request.url.path.startswith("/api/"):
        if not await rate_limiter.check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests", "detail": "Please try again later"}
            )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        logger.error(f"Error in middleware: {str(e)}")
        error_counter.labels(error_type="middleware_error").inc()
        raise


@app.get("/")
async def read_root():
    return FileResponse("static/index.html")


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """Process a natural language query with comprehensive error handling"""
    query_start_time = time.time()
    query_counter.inc()

    try:
        # Get or create session ID
        session_id = request.session_id or memory_service.create_session()
        active_sessions.inc()

        # Get conversation history
        history = memory_service.get_conversation_history(session_id)

        # Submit task to Celery for async processing
        task = process_query_task.delay(
            request.query,
            session_id,
            history
        )

        # Wait for result with timeout
        try:
            result = task.get(timeout=30)
        except Exception as e:
            logger.error(f"Task timeout or error: {str(e)}")
            raise HTTPException(status_code=504, detail="Query processing timeout")

        if result.get("error"):
            error_counter.labels(error_type="query_error").inc()
            raise HTTPException(status_code=500, detail=result["error"])

        # Store in conversation memory
        memory_service.add_to_history(
            session_id,
            request.query,
            result["answer"],
            result["sql_query"]
        )

        # Generate suggestions in background
        suggestions = []
        if result.get("success", False):
            suggestions = suggestion_service.generate_suggestions(
                request.query,
                result["answer"],
                history
            )

        # Record query latency
        query_duration = time.time() - query_start_time
        query_latency.observe(query_duration)

        # Schedule session cleanup in background
        background_tasks.add_task(memory_service.extend_session, session_id)

        return QueryResponse(
            answer=result["answer"],
            sql_query=result["sql_query"],
            suggestions=suggestions,
            session_id=session_id,
            execution_time=query_duration
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        error_counter.labels(error_type="general_error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        active_sessions.dec()


@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = memory_service.get_conversation_history(session_id)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schema")
async def get_schema():
    """Get database schema information with caching"""
    try:
        schema_info = sql_agent.get_schema_info()
        return {"schema": schema_info}
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Database unavailable")
    except Exception as e:
        logger.error(f"Error getting schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "components": {}
    }

    # Check database connection
    try:
        sql_agent.get_schema_info()
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Check Redis connection
    try:
        memory_service.redis_client.ping()
        health_status["components"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Check system resources
    health_status["components"]["system"] = {
        "status": "healthy",
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

    if health_status["components"]["system"]["cpu_percent"] > 90:
        health_status["components"]["system"]["status"] = "warning"

    if health_status["components"]["system"]["memory_percent"] > 90:
        health_status["components"]["system"]["status"] = "warning"

    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Cleanup tasks on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down application")
    # Add any cleanup tasks here