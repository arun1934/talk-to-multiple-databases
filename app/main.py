from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import json

from .services.memory_service import MemoryService
from .services.suggestion_service import SuggestionService
from .tasks import process_query_task
from .agents.sql_agent import SQLAgent
from .graphs.correction_graph import create_correction_graph

app = FastAPI(title="SQL Chat Agent")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
memory_service = MemoryService()
suggestion_service = SuggestionService()
sql_agent = SQLAgent()

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sql_query: str
    suggestions: List[str]
    session_id: str

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a natural language query and return results"""
    try:
        # Get or create session ID
        session_id = request.session_id or memory_service.create_session()
        
        # Get conversation history
        history = memory_service.get_conversation_history(session_id)
        
        # Submit task to Celery for async processing
        task = process_query_task.delay(
            request.query,
            session_id,
            history
        )
        
        # Wait for result (in production, you might want to use websockets or polling)
        result = task.get(timeout=30)
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Store in conversation memory
        memory_service.add_to_history(
            session_id, 
            request.query, 
            result["answer"],
            result["sql_query"]
        )
        
        # Generate suggestions based on context
        suggestions = suggestion_service.generate_suggestions(
            request.query,
            result["answer"],
            history
        )
        
        return QueryResponse(
            answer=result["answer"],
            sql_query=result["sql_query"],
            suggestions=suggestions,
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = memory_service.get_conversation_history(session_id)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/schema")
async def get_schema():
    """Get database schema information"""
    try:
        schema_info = sql_agent.get_schema_info()
        return {"schema": schema_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
