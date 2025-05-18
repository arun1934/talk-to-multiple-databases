"""
Configuration Module

Loads application settings from environment variables with sensible defaults.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database settings
DATABASE = {
    "url": os.getenv("DATABASE_URL", "postgresql://postgres:admin@host.docker.internal/NPS"),
    "nps_url": os.getenv("DATABASE_URL_NPS", "postgresql://postgres@postgres-nps:5432/nps_db"),
    "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "300")),
}

# Redis settings
REDIS = {
    "url": os.getenv("REDIS_URL", "redis://redis:6379/0"),
    "host": os.getenv("REDIS_HOST", "redis"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "use_cluster": os.getenv("USE_REDIS_CLUSTER", "false").lower() == "true",
}

# Celery settings
CELERY = {
    "broker_url": os.getenv("CELERY_BROKER_URL", f"redis://{REDIS['host']}:{REDIS['port']}/1"),
    "result_backend": os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS['host']}:{REDIS['port']}/2"),
    "task_time_limit": int(os.getenv("TASK_TIME_LIMIT", "60")),
    "task_soft_time_limit": int(os.getenv("TASK_SOFT_TIME_LIMIT", "50")),
    "worker_prefetch_multiplier": int(os.getenv("WORKER_PREFETCH_MULTIPLIER", "1")),
    "worker_max_tasks_per_child": int(os.getenv("WORKER_MAX_TASKS_PER_CHILD", "1000")),
    "worker_max_memory_per_child": int(os.getenv("WORKER_MAX_MEMORY_PER_CHILD", "200000")),
}

# LLM settings (LiteLLM)
LLM = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "api_base": os.getenv("LITELLM_API_BASE", "https://lmlitellm.landmarkgroup.com"),
    "auth_header": os.getenv("LITELLM_AUTH_HEADER", f"Bearer {os.getenv('OPENAI_API_KEY', '')}"),
    "model": os.getenv("LITELLM_MODEL", "gpt-4.1-mini"),
    "generation_temperature": float(os.getenv("GENERATION_TEMPERATURE", "0.0")),
    "summary_temperature": float(os.getenv("SUMMARY_TEMPERATURE", "0.3")),
    "suggestion_temperature": float(os.getenv("SUGGESTION_TEMPERATURE", "0.5")),
    "rate_limit": int(os.getenv("LLM_RATE_LIMIT", "60")),
    "failure_threshold": int(os.getenv("LLM_FAILURE_THRESHOLD", "5")),
    "reset_timeout": int(os.getenv("LLM_RESET_TIMEOUT", "30")),
}

# Cache settings
CACHE = {
    "enable_llm_cache": os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true",
    "llm_cache_ttl": int(os.getenv("LLM_CACHE_TTL", "300")),
    "query_cache_ttl": int(os.getenv("QUERY_CACHE_TTL", "300")),
    "schema_cache_ttl": int(os.getenv("SCHEMA_CACHE_TTL", "3600")),
}

# API settings
API = {
    "rate_limit_per_minute": int(os.getenv("API_RATE_LIMIT", "30")),
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
}

# Memory Service settings
MEMORY = {
    "session_ttl": int(os.getenv("SESSION_TTL", "86400")),  # 24 hours
    "history_limit": int(os.getenv("HISTORY_LIMIT", "10")),
    "retry_delay": int(os.getenv("REDIS_RETRY_DELAY", "1")),
    "max_retries": int(os.getenv("REDIS_MAX_RETRIES", "3")),
}

# Logging settings
LOGGING = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
}


# Helper function to get nested config
def get_config(path: str, default: Any = None) -> Any:
    """
    Get a configuration value by dot notation path
    Example: get_config("LLM.model") returns the model from LLM config
    """
    config = {
        "DATABASE": DATABASE,
        "REDIS": REDIS,
        "CELERY": CELERY,
        "LLM": LLM,
        "CACHE": CACHE,
        "API": API,
        "MEMORY": MEMORY,
        "LOGGING": LOGGING,
    }

    parts = path.split(".")
    result = config

    try:
        for part in parts:
            result = result[part]
        return result
    except (KeyError, TypeError):
        return default