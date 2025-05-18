import redis
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta  # Add timedelta here
import os
import logging
from functools import wraps
import time

from app.config import REDIS, MEMORY, CACHE

logger = logging.getLogger(__name__)

def json_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)

def with_redis_fallback(func):
    """Decorator to handle Redis connection failures gracefully"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error in {func.__name__}: {str(e)}")
            # Return sensible defaults instead of failing
            if func.__name__ == 'get_conversation_history':
                return []
            elif func.__name__ == 'create_session':
                return str(uuid.uuid4())
            elif func.__name__ == 'get_cached_query':
                return None
            else:
                return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise

    return wrapper


class MemoryService:
    def __init__(self):
        self.redis_url = REDIS["url"]
        self.session_ttl = MEMORY["session_ttl"]
        self.history_limit = MEMORY["history_limit"]
        self.max_retries = MEMORY["max_retries"]
        self.retry_delay = MEMORY["retry_delay"]

        self._connect_with_retry()

    def _connect_with_retry(self):
        """Connect to Redis with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.redis_client = redis.Redis(
                    host=REDIS["host"],
                    port=REDIS["port"],
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Successfully connected to Redis")
                return
            except redis.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Redis connection attempt {attempt + 1} failed, retrying...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"Failed to connect to Redis after {self.max_retries} attempts")
                    # Create a dummy client that will fail operations gracefully
                    self.redis_client = None

    @with_redis_fallback
    def create_session(self) -> str:
        """Create a new session ID with error handling"""
        session_id = str(uuid.uuid4())

        try:
            session_data = {
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "query_count": 0
            }

            self.redis_client.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_data)
            )

            logger.info(f"Created new session: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return session_id  # Return the ID even if Redis fails

    def add_to_history(self, session_id: str, query: str, answer: str, sql_query: str):
        """Add a conversation to history with error handling"""
        try:
            history_key = f"history:{session_id}"

            # Create conversation entry
            conversation = {
                "timestamp": datetime.utcnow().isoformat(),
                "query": query,
                "answer": answer,
                "sql_query": sql_query
            }

            # Add to Redis list
            self.redis_client.lpush(history_key, json.dumps(conversation))

            # Trim to keep only last N conversations
            # This is the key line to ensure we keep the last 5 conversations
            self.redis_client.ltrim(history_key, 0, self.history_limit - 1)

            # Set expiry on the history
            self.redis_client.expire(history_key, self.session_ttl)

            # Update session info
            session_key = f"session:{session_id}"
            if self.redis_client.exists(session_key):
                session_data = json.loads(self.redis_client.get(session_key))
                session_data["last_activity"] = datetime.utcnow().isoformat()
                session_data["query_count"] = session_data.get("query_count", 0) + 1
                self.redis_client.setex(session_key, self.session_ttl, json.dumps(session_data))

            logger.debug(f"Added conversation to history for session {session_id}")

        except Exception as e:
            logger.error(f"Error adding to history: {str(e)}")

    @with_redis_fallback
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history with error handling"""
        try:
            history_key = f"history:{session_id}"

            # Check if session exists
            if not self.redis_client.exists(f"session:{session_id}"):
                logger.warning(f"Session {session_id} does not exist")
                return []

            # Get history from Redis
            history_raw = self.redis_client.lrange(history_key, 0, -1)

            # Parse and reverse to get chronological order
            history = []
            for item in reversed(history_raw):
                try:
                    history.append(json.loads(item))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse history item: {str(e)}")
                    continue

            return history

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    @with_redis_fallback
    def get_cached_query(self, session_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Get cached query result with error handling"""
        try:
            # Normalize query by removing whitespace and converting to lowercase
            normalized_query = " ".join(query.lower().split())

            # Use a simple hash function less prone to variation
            import hashlib
            query_hash = hashlib.md5(normalized_query.encode()).hexdigest()

            cache_key = f"query_result:{session_id}:{query_hash}"

            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                try:
                    logger.info(f"Cache hit for query in session {session_id}")
                    return json.loads(cached_result)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse cached query: {str(e)}")
                    return None
            return None

        except Exception as e:
            logger.error(f"Error getting cached query: {str(e)}")
            return None

    @with_redis_fallback
    def cache_query_result(self, session_id: str, query: str, result: Dict[str, Any], ttl: int = None):
        """Cache a query result with error handling"""
        if ttl is None:
            ttl = CACHE["query_cache_ttl"]

        try:
            cache_key = f"query_result:{session_id}:{hash(query)}"

            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )

            logger.debug(f"Cached query result for session {session_id}")

        except Exception as e:
            logger.error(f"Error caching query result: {str(e)}")

    @with_redis_fallback
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session with error handling"""
        try:
            history_key = f"history:{session_id}"
            session_key = f"session:{session_id}"

            total_queries = self.redis_client.llen(history_key)

            # Get session data
            session_data = None
            if self.redis_client.exists(session_key):
                try:
                    session_data = json.loads(self.redis_client.get(session_key))
                except json.JSONDecodeError:
                    session_data = None

            stats = {
                "session_id": session_id,
                "total_queries": total_queries,
                "created_at": session_data.get("created_at") if session_data else None,
                "last_activity": session_data.get("last_activity") if session_data else None,
                "ttl": self.redis_client.ttl(session_key)
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting session stats: {str(e)}")
            return {
                "session_id": session_id,
                "total_queries": 0,
                "created_at": None,
                "last_activity": None,
                "ttl": -1
            }

    @with_redis_fallback
    def extend_session(self, session_id: str):
        """Extend a session's TTL with error handling"""
        try:
            session_key = f"session:{session_id}"
            history_key = f"history:{session_id}"

            if self.redis_client.exists(session_key):
                # Update last activity
                session_data = json.loads(self.redis_client.get(session_key))
                session_data["last_activity"] = datetime.utcnow().isoformat()

                # Extend TTL
                self.redis_client.setex(session_key, self.session_ttl, json.dumps(session_data))

                if self.redis_client.exists(history_key):
                    self.redis_client.expire(history_key, self.session_ttl)

                logger.debug(f"Extended session {session_id}")
            else:
                logger.warning(f"Attempted to extend non-existent session {session_id}")

        except Exception as e:
            logger.error(f"Error extending session: {str(e)}")

    @with_redis_fallback
    def clear_session(self, session_id: str):
        """Clear a session and its history with error handling"""
        try:
            # Delete session and history
            self.redis_client.delete(f"session:{session_id}")
            self.redis_client.delete(f"history:{session_id}")

            # Delete any cached queries for this session
            pattern = f"query_result:{session_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)

            logger.info(f"Cleared session {session_id}")

        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")

    @with_redis_fallback
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (called periodically)"""
        try:
            # Find all session keys
            session_keys = self.redis_client.keys("session:*")
            cleaned = 0

            for key in session_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    continue
                elif ttl == -1:  # No expiry set
                    # Set expiry for keys without TTL
                    self.redis_client.expire(key, self.session_ttl)
                elif ttl <= 0:
                    # Clean up expired session
                    session_id = key.split(":", 1)[1]
                    self.clear_session(session_id)
                    cleaned += 1

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions")

        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")

    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            return self.redis_client.ping()
        except:
            return False