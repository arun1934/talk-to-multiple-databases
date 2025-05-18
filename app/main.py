from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, HTTPException,Request
from fastapi.responses import HTMLResponse, JSONResponse,Response, RedirectResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
from msal import ConfidentialClientApplication
import os
import json
import logging
import time
import re
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil
import redis

from app.services.memory_service import MemoryService
from app.services.suggestion_service import SuggestionService
from app.services.visualization_service import VisualizationService
from app.tasks import process_query_task
from app.agents.sql_agent import SQLAgent, DatabaseConnectionError, QueryExecutionError, AIServiceError
from app.graphs.correction_graph import create_correction_graph
from app.tasks import process_query_task

# Import config
from app.config import API, LOGGING, REDIS, MEMORY, CACHE

from datetime import datetime, timedelta
from pathlib import Path

# QUERY_LOG_FILE = "query_log.jsonl" # Old definition
QUERY_LOG_FILE = Path(__file__).parent / "query_log.jsonl" # New definition

MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_TENANT_ID = os.getenv("MS_TENANT_ID")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI", "http://localhost:8003/auth/callback")
AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT_ID}"
SCOPE = ["user.read"]

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING["level"]),
    format=LOGGING["format"]
)
logger = logging.getLogger(__name__)

# Helper function for logging query details
def log_query_details(log_entry: Dict[str, Any]):
    try:
        with open(QUERY_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write to query log file: {e}")

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
    allow_origins=API["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration
from collections import defaultdict
import asyncio


class RateLimiter:
    def __init__(self, requests_per_minute=API["rate_limit_per_minute"]):
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


rate_limiter = RateLimiter(requests_per_minute=API["rate_limit_per_minute"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
memory_service = MemoryService()
suggestion_service = SuggestionService()
sql_agent = SQLAgent()
visualization_service = VisualizationService()


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
    results: Optional[Dict[str, Any]] = None


class VisualizationRequest(BaseModel):
    question: str
    sqlQuery: str
    results: Dict[str, Any]


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



class AccessTokenMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # request = Request(scope, receive) # No longer needed for this bypassed version
            # Skip token check for public routes AND metrics
            # if request.url.path in ["/signIn", "/login", "/auth/callback", "/metrics", "/health"] or request.url.path.startswith("/static"):
            #     await self.app(scope, receive, send)
            #     return
            #
            # # Check for access_token in cookies
            # access_token = request.cookies.get("access_token")
            # if not access_token:
            #     # Redirect to login if token is not present send to login.html
            #     response = RedirectResponse(url="/signIn")
            #     await response(scope, receive, send)
            #     return
            # Authentication bypassed
            await self.app(scope, receive, send)
            return

        await self.app(scope, receive, send)

@app.get("/login")
async def login(request: Request):
    # Construct MS_REDIRECT_URI dynamically
    dynamic_redirect_uri = f"{request.url.scheme}://{request.url.netloc}/auth/callback"
    logger.info(f"Dynamic MS_REDIRECT_URI for /login: {dynamic_redirect_uri}")

    cca = ConfidentialClientApplication(
        MS_CLIENT_ID, authority=AUTHORITY, client_credential=MS_CLIENT_SECRET
    )
    auth_url = cca.get_authorization_request_url(
        SCOPE, redirect_uri=dynamic_redirect_uri
    )
    return RedirectResponse(auth_url)

@app.get("/signin", response_class=HTMLResponse, include_in_schema=False)
async def login_html_lowercase(request: Request):
    path = Path(__file__).parent.parent / "static/login.html"
    with open(path, "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/signIn", response_class=HTMLResponse)
async def login_html(request: Request):
    path = Path(__file__).parent.parent / "static/login.html"
    with open(path, "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("No code returned", status_code=400)

    # Construct MS_REDIRECT_URI dynamically for validation
    dynamic_redirect_uri = f"{request.url.scheme}://{request.url.netloc}/auth/callback"
    logger.info(f"Dynamic MS_REDIRECT_URI for /auth/callback: {dynamic_redirect_uri}")

    cca = ConfidentialClientApplication(
        MS_CLIENT_ID, authority=AUTHORITY, client_credential=MS_CLIENT_SECRET
    )
    result = cca.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=dynamic_redirect_uri,
    )
    if "id_token_claims" in result:
        user_email = result["id_token_claims"].get("preferred_username")
        user_name = result["id_token_claims"].get("name")
        expires_in = result.get("expires_in", 3600)  # Default to 1 hour if not provided
        expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)

        print ("User Email", user_email)
        print("username", user_name)
        response = RedirectResponse(url="/home")
        
        response.set_cookie("access_token", result["access_token"], expires=expires_in)
        response.set_cookie(key="user_email", value=user_email, expires=expires_in)
        response.set_cookie(key="user_name", value=user_name, expires=expires_in)


        return response
    else:
        return HTMLResponse("Error logging in", status_code=401)


@app.get("/")
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    user_email = request.cookies.get("user_email") or "user@example.com" # Default value
    user_name = request.cookies.get("user_name") or "Test User" # Default value
    # No redirect if user_email is not found

    # add json to index.html using templates
    path = Path(__file__).parent.parent / "static/index.html"
    with open(path, "r") as f:
        content = f.read()
        
        # Safely get initial from username
        initial = ""
        if user_name:
            parts = user_name.split(" ")
            if len(parts) == 1:
                initial = parts[0][0] if parts[0] else ""
            elif len(parts) > 1:
                initial = (parts[0][0] if parts[0] else "") + (parts[1][0] if parts[1] else "")
        initial = initial.upper() if initial else "TU" # Default initial if extraction fails


        content = content.replace("{{ user_email }}", user_email)
        content = content.replace("{{ user_name }}", user_name)
        content = content.replace("{{ initial }}", initial)
        return HTMLResponse(content=content, status_code=200)


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks, req: Request):
    """Process a natural language query with comprehensive error handling"""
    query_start_time = time.time()
    query_counter.inc()

    try:
        # Get or create persistent session ID from cookie
        session_id = request.session_id
        response_cookies = {}

        if not session_id:
            # If no session ID provided, check for cookie
            session_cookie = req.cookies.get("query_session_id")
            if session_cookie:
                session_id = session_cookie
                logger.info(f"Using existing session from cookie: {session_id}")
            else:
                # Create new session ID if none exists
                session_id = memory_service.create_session()
                logger.info(f"Created new session: {session_id}")
                # Set cookie for future requests
                response_cookies["query_session_id"] = session_id

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

        # Log query details to file
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "nl_query": request.query,
            "sql_query_generated": result["sql_query"],
            "nl_response": result["answer"],
            "suggestions": suggestions,
            "raw_results_preview": result.get("results", {}).get("rows", [])[:10] # Log first 10 rows of results as preview
        }
        log_query_details(log_data)

        response = QueryResponse(
            answer=result["answer"],
            sql_query=result["sql_query"],
            suggestions=suggestions,
            session_id=session_id,
            execution_time=query_duration,
            results=result.get("results")
        )

        # Create the response and set cookies if needed
        response_obj = JSONResponse(content=jsonable_encoder(response))

        # Set session cookie if needed
        if "query_session_id" in response_cookies:
            response_obj.set_cookie(
                key="query_session_id",
                value=response_cookies["query_session_id"],
                httponly=True,
                max_age=MEMORY["session_ttl"],  # Use your session TTL from config
                samesite="lax"  # Can be "strict", "lax", or "none"
            )

        return response_obj

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        error_counter.labels(error_type="general_error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        active_sessions.dec()


@app.post("/api/visualization-recommendation")
async def visualization_recommendation(request: VisualizationRequest):
    """Get a visualization recommendation for SQL query results"""
    try:
        logger.info(f"Visualization recommendation requested for question: {request.question}")

        recommendation = await visualization_service.recommend_visualization(
            question=request.question,
            sql_query=request.sqlQuery,
            results=request.results
        )

        logger.debug(f"Visualization recommendation: {recommendation.model_dump_json(indent=2)}")
        return recommendation

    except Exception as e:
        logger.error(f"Error recommending visualization: {str(e)}", exc_info=True)
        error_counter.labels(error_type="visualization_error").inc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating visualization recommendation: {str(e)}"
        )


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


# Update the metrics endpoint in main.py
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to add process time header and handle rate limiting"""
    start_time = time.time()
    client_ip = request.client.host

    # Skip rate limiting for metrics endpoint
    if request.url.path == "/metrics":
        response = await call_next(request)
        return response

    # Check rate limit for API endpoints
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

@app.post("/api/debug/clear-cache", include_in_schema=False)
async def clear_cache():
    """Debug endpoint to clear SQL query cache"""
    try:
        from app.agents.sql_agent import SQLAgent
        sql_agent = SQLAgent()
        sql_agent.clear_query_cache()
        return {"status": "success", "message": "SQL query cache cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Cleanup tasks on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down application")
    # Add any cleanup tasks here


@app.on_event("startup")
async def startup_event():
    """Initialize connections and verify Redis is accessible"""
    try:
        # Test Redis connection
        redis_client = redis.Redis(
            host=REDIS["host"],
            port=REDIS["port"],
            socket_timeout=2,
            socket_connect_timeout=2
        )
        response = redis_client.ping()
        if response:
            logger.info("Redis connection successful")
        else:
            logger.error("Redis connection failed - ping returned falsy value")
    except Exception as e:
        logger.error(f"Failed to connect to Redis during startup: {str(e)}")

