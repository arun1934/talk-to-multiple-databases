import redis
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

class MemoryService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            decode_responses=True
        )
        self.session_ttl = 3600 * 24  # 24 hours
        self.history_limit = 10  # Keep last 10 conversations
    
    def create_session(self) -> str:
        """Create a new session ID"""
        session_id = str(uuid.uuid4())
        self.redis_client.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps({"created_at": datetime.utcnow().isoformat()})
        )
        return session_id
    
    def add_to_history(self, session_id: str, query: str, answer: str, sql_query: str):
        """Add a conversation to history"""
        history_key = f"history:{session_id}"
        
        conversation = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "answer": answer,
            "sql_query": sql_query
        }
        
        # Add to Redis list
        self.redis_client.lpush(history_key, json.dumps(conversation))
        
        # Trim to keep only last N conversations
        self.redis_client.ltrim(history_key, 0, self.history_limit - 1)
        
        # Set expiry on the history
        self.redis_client.expire(history_key, self.session_ttl)
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        history_key = f"history:{session_id}"
        
        # Check if session exists
        if not self.redis_client.exists(f"session:{session_id}"):
            return []
        
        # Get history from Redis
        history_raw = self.redis_client.lrange(history_key, 0, -1)
        
        # Parse and reverse to get chronological order
        history = []
        for item in reversed(history_raw):
            try:
                history.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        
        return history
    
    def get_cached_query(self, session_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Get cached query result if available"""
        cache_key = f"query_result:{session_id}:{hash(query)}"
        
        cached_result = self.redis_client.get(cache_key)
        if cached_result:
            try:
                return json.loads(cached_result)
            except json.JSONDecodeError:
                return None
        return None
    
    def cache_query_result(self, session_id: str, query: str, result: Dict[str, Any], ttl: int = 300):
        """Cache a query result"""
        cache_key = f"query_result:{session_id}:{hash(query)}"
        self.redis_client.setex(
            cache_key,
            ttl,
            json.dumps(result)
        )
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        history_key = f"history:{session_id}"
        
        total_queries = self.redis_client.llen(history_key)
        
        # Get session creation time
        session_data = self.redis_client.get(f"session:{session_id}")
        if session_data:
            session_info = json.loads(session_data)
            created_at = session_info.get("created_at")
        else:
            created_at = None
        
        return {
            "session_id": session_id,
            "total_queries": total_queries,
            "created_at": created_at,
            "ttl": self.redis_client.ttl(f"session:{session_id}")
        }
    
    def extend_session(self, session_id: str):
        """Extend a session's TTL"""
        session_key = f"session:{session_id}"
        history_key = f"history:{session_id}"
        
        if self.redis_client.exists(session_key):
            self.redis_client.expire(session_key, self.session_ttl)
            self.redis_client.expire(history_key, self.session_ttl)
    
    def clear_session(self, session_id: str):
        """Clear a session and its history"""
        self.redis_client.delete(f"session:{session_id}")
        self.redis_client.delete(f"history:{session_id}")
