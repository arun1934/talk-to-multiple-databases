# Developer Guide - SQL DB Chat System

This guide provides essential information for developers working on the SQL DB Chat System.

## 1. Project Structure

```
sql-db-chat/
├── app/
│   ├── agents/
│   │   └── sql_agent.py         # Core SQL translation agent
│   ├── config/
│   │   ├── llm_config.py        # LLM integration configuration
│   │   └── settings.py          # Application settings
│   ├── cache/
│   │   └── redis_cache.py       # Redis caching utilities
│   ├── memory/
│   │   └── conversation_memory.py # Conversation history management
│   ├── routers/
│   │   └── agent.py             # API endpoint definitions
│   ├── celery_worker.py         # Celery worker configuration
│   ├── main.py                  # FastAPI application entry point
│   └── tasks.py                 # Celery task definitions
├── requirements.txt             # Project dependencies
├── Dockerfile                   # Docker configuration
└── docker-compose.yml           # Docker Compose configuration
```

## 2. Development Setup

### Local Development Environment

1. **Clone the repository**:
   ```bash
   git clone [repository-url]
   cd sql-db-chat
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (create a `.env` file):
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:admin@localhost/YourDB
   REDIS_URL=redis://localhost:6379/0
   REDIS_HOST=localhost
   REDIS_PORT=6379
   OPENAI_API_KEY=your_api_key
   LITELLM_API_BASE=https://lmlitellm.landmarkgroup.com
   LITELLM_AUTH_HEADER=Bearer your_auth_header
   LITELLM_MODEL=landmark-gpt-4o-mini
   ENABLE_LLM_CACHE=true
   LLM_CACHE_TTL=300
   GENERATION_TEMPERATURE=0.0
   SUMMARY_TEMPERATURE=0.3
   SUGGESTION_TEMPERATURE=0.5
   ```

5. **Run Redis locally**:
   ```bash
   docker run -d -p 6379:6379 redis
   ```

6. **Run the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Run Celery worker** (in a separate terminal):
   ```bash
   celery -A app.celery_worker worker --loglevel=info
   ```

### Docker Development Environment

1. **Build the Docker containers**:
   ```bash
   docker-compose build
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f
   ```

## 3. Core Components

### 3.1 SQL Agent

The `SQLAgent` class in `app/agents/sql_agent.py` is the core component responsible for processing natural language queries. It follows a state machine approach using LangGraph to orchestrate the process:

1. Table selection
2. Schema retrieval
3. SQL generation
4. Query execution
5. Result formatting
6. Follow-up suggestion

**Key Methods**:

- `handle()`: Main entry point for processing a query
- `choose_tables()`: Selects relevant tables for a question
- `generate_sql()`: Converts natural language to SQL
- `format_results_as_natural_language()`: Formats query results
- `suggest_followups()`: Generates follow-up questions

### 3.2 LLM Configuration

The `app/config/llm_config.py` module provides centralized LLM integration:

```python
# Access settings from the central settings file
enable_caching = settings.enable_llm_cache
cache_ttl = settings.llm_cache_ttl

# Get auth header from environment variable if not in settings
auth_header = settings.litellm_auth_header
if not auth_header:
    auth_header = os.getenv("AUTH_HEADER", "")

# Set up the LLM
llm = ChatOpenAI(
    openai_api_base=settings.litellm_api_base,
    default_headers={
        "Authorization": auth_header,
    },
    model=settings.litellm_model,
    api_key=settings.openai_api_key,
    temperature=0  # Default temperature, will be overridden in specific calls
)

# LLM Configuration class
class LLMConfig:
    def __init__(self):
        self.enable_caching = settings.enable_llm_cache
        self.cache_ttl = settings.llm_cache_ttl
        self.generation_temperature = settings.generation_temperature
        self.summary_temperature = settings.summary_temperature
        self.suggestion_temperature = settings.suggestion_temperature

llm_config = LLMConfig()
```

The `call_llm()` function is the standard interface for all LLM calls:

```python
async def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0):
    # Create a copy of the LLM with the specific temperature for this call
    configured_llm = llm.with_config({"temperature": temperature})
    
    # Format the messages array
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Make the API call
    response = await configured_llm.ainvoke(messages)
    
    # Extract and return the content
    return response.content
```

### 3.3 API Endpoints

The API endpoints are defined in `app/routers/agent.py`:

- `POST /query`: Submit a natural language question
- `GET /result/{task_id}`: Retrieve the results
- `POST /visualization-recommendation`: Get visualization suggestions

### 3.4 Asynchronous Processing

The system uses Celery for asynchronous processing. Tasks are defined in `app/tasks.py`:

```python
@celery_app.task
def process_nl_query(question, session_id=None):
    # Create an event loop for async code
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create a new session for this task
    async def run_query():
        async with async_session() as session:
            agent = SQLAgent(session, session_id)
            sql, formatted_result, suggestions, table_result = await agent.handle(question)
            return {
                "sql": sql,
                "formatted_result": formatted_result,
                "suggestions": suggestions,
                "table_result": table_result
            }
    
    # Run the async function and return the result
    return loop.run_until_complete(run_query())
```

## 4. Development Workflows

### 4.1 Adding a New Endpoint

1. Create a new route in `app/routers/agent.py`:

```python
@router.post("/new-endpoint", response_model=YourResponseModel)
async def new_endpoint(request: YourRequestModel):
    try:
        # Your endpoint logic here
        return YourResponseModel(...)
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

2. Define request/response models in the same file:

```python
class YourRequestModel(BaseModel):
    field1: str
    field2: Optional[int] = None

class YourResponseModel(BaseModel):
    result: str
```

### 4.2 Modifying SQL Agent Behavior

To modify how the SQL Agent processes queries:

1. Update the appropriate method in `app/agents/sql_agent.py`
2. Adjust the system/user prompts in the method to change LLM behavior
3. Add or modify the state graph nodes if changing the workflow

Example of adding a new node to the state graph:

```python
async def my_new_node(state: GraphState) -> dict:
    # Process the state
    result = await self.my_new_method(state['some_data'])
    return {'new_state_key': result}

graph.add_node('my_new_node', my_new_node)
graph.add_edge('previous_node', 'my_new_node')
graph.add_edge('my_new_node', 'next_node')
```

### 4.3 Integrating a New LLM Provider

To add support for a different LLM provider:

1. Update `app/config/settings.py` with new provider settings:

```python
# New provider settings
new_provider_api_base: str = ""
new_provider_auth_header: str = ""
new_provider_model: str = ""
```

2. Modify `app/config/llm_config.py` to support the new provider:

```python
# Conditional setup based on provider
if settings.use_new_provider:
    from langchain_newprovider import ChatNewProvider
    llm = ChatNewProvider(
        api_base=settings.new_provider_api_base,
        auth_header=settings.new_provider_auth_header,
        model=settings.new_provider_model,
        # Other provider-specific settings
    )
else:
    # Existing LiteLLM setup
    llm = ChatOpenAI(...)
```

## 5. Testing

### 5.1 Manual API Testing

Use the FastAPI Swagger UI at `/docs` to test endpoints:

1. Navigate to `http://localhost:8000/docs`
2. Select an endpoint
3. Click "Try it out"
4. Fill in the request parameters
5. Execute and view the response

### 5.2 Testing with curl

```bash
# Submit a query
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "How many users do we have?", "session_id": "test-session"}'

# Get the result
curl "http://localhost:8000/result/{task_id}"

# Visualization recommendation
curl -X POST "http://localhost:8000/visualization-recommendation" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me monthly sales", "sqlQuery": "SELECT month, SUM(sales) FROM sales GROUP BY month", "results": "[{\"month\": \"Jan\", \"sum\": 1200}, {\"month\": \"Feb\", \"sum\": 1500}]"}'
```


## 6. Performance Optimization

### 6.1 Database Query Optimization

1. **Identify slow queries** by logging execution times:

```python
async def execute_sql(self, sql: str):
    start_time = time.time()
    result = await self.session.execute(text(sql))
    execution_time = time.time() - start_time
    
    if execution_time > 1.0:  # Log slow queries (>1 second)
        print(f"Slow query ({execution_time:.2f}s): {sql}")
        
    return result
```

2. **Add indexes** to commonly queried columns in your database

3. **Use query hints** for complex queries:

```python
# Example with query hint
sql = """
SELECT /*+ INDEX(users user_email_idx) */
  id, email, name
FROM users
WHERE email LIKE :email
"""
```

### 6.2 Caching Strategies

1. **Implement semantic caching** by normalizing similar queries:

```python
def _generate_semantic_cache_key(self, question: str) -> str:
    """Generate a cache key based on semantic meaning of the question"""
    # Use LLM to generate a normalized question
    normalized = await call_llm(
        system_prompt="Normalize this question to its core intent, removing specific values.",
        user_prompt=f"Original question: {question}"
    )
    return f"semantic:{hashlib.md5(normalized.encode()).hexdigest()}"
```

2. **Implement tiered caching** with different TTLs:

```python
async def cache_response(self, question, sql, result, ttl=None):
    # Determine appropriate TTL based on query type
    if "COUNT(*)" in sql.upper():
        # Count queries might change frequently
        ttl = ttl or 60  # 1 minute
    elif "ORDER BY" in sql.upper() and "LIMIT" in sql.upper():
        # Paginated results
        ttl = ttl or 300  # 5 minutes
    else:
        # Standard queries
        ttl = ttl or 3600  # 1 hour
        
    await set_cache(self._generate_cache_key(question), result, ttl)
```

## 7. Common Development Tasks

### 7.1 Updating System Prompts

System prompts are critical for LLM performance. When updating prompts:

1. Keep prompts clear and specific
2. Test different variations to find optimal wording
3. Include examples for complex tasks
4. Structure prompts with clear sections
5. Update the relevant method in `sql_agent.py`

Example of updating the SQL generation prompt:

```python
system_prompt = """You are an expert SQL developer specializing in PostgreSQL.
Generate precise SQL queries based on the provided schema and question.

Guidelines:
1. Use explicit column names instead of SELECT *
2. Include appropriate JOINs when querying multiple tables
3. Add clear aliases for complex queries
4. Use appropriate aggregation functions for summary questions
5. Include ORDER BY for questions about "top", "highest", "lowest", etc.
6. Use proper parameterization for any values
"""
```

### 7.2 Adding New Database Functionality

To add support for new database features:

1. Update the `get_ddls()` method to include new schema information
2. Modify system prompts to instruct the LLM about the new features
3. Add specialized formatting for the new data types if needed

### 7.3 Customizing Visualization Recommendations

To enhance visualization recommendations:

1. Update the system prompt in `agent.py`:

```python
system_prompt = """You are an AI assistant that recommends appropriate data visualizations.

Available chart types:
- Bar Graphs: Best for comparing categorical data
- Line Graphs: Best for time series data and trends
- Pie Charts: Best for showing proportions of a whole
- Scatter Plots: Best for showing relationships between two variables
- Heat Maps: Best for showing patterns in complex datasets
- Box Plots: Best for showing distributions and outliers
"""
```

2. Add support for additional chart types in the frontend

## 8. Deployment Considerations

### 8.1 Production Environment

1. **Docker Compose for Production**:

```yaml
version: '3'

services:
  app:
    build: .
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LITELLM_API_BASE=${LITELLM_API_BASE}
      - LITELLM_AUTH_HEADER=${LITELLM_AUTH_HEADER}
      - LITELLM_MODEL=${LITELLM_MODEL}
      - ENABLE_LLM_CACHE=${ENABLE_LLM_CACHE}
      - LLM_CACHE_TTL=${LLM_CACHE_TTL}
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - celery_worker

  celery_worker:
    build: .
    restart: always
    command: celery -A app.celery_worker worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LITELLM_API_BASE=${LITELLM_API_BASE}
      - LITELLM_AUTH_HEADER=${LITELLM_AUTH_HEADER}
      - LITELLM_MODEL=${LITELLM_MODEL}
      - ENABLE_LLM_CACHE=${ENABLE_LLM_CACHE}
      - LLM_CACHE_TTL=${LLM_CACHE_TTL}
    depends_on:
      - redis

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

2. **Environment Variables** using a `.env` file:

Create a production `.env` file with secure values stored in a secure location (not in version control).

### 8.2 Scaling Considerations

1. **Horizontal Scaling**:

- Scale Celery workers independently for handling more concurrent requests:
  ```yaml
  celery_worker:
    deploy:
      replicas: 3
  ```

2. **Database Scaling**:

- Consider read replicas for heavy query loads
- Implement connection pooling using PgBouncer
- Set explicit timeouts for database queries

3. **Redis Scaling**:

- Consider Redis Cluster for high availability
- Implement Redis Sentinel for failover
- Monitor Redis memory usage and adjust maxmemory settings

### 8.3 Monitoring and Logging

1. **Add Prometheus metrics** for monitoring:

```python
from prometheus_client import Counter, Histogram
import time

# Define metrics
REQUEST_COUNT = Counter('sql_chat_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('sql_chat_request_latency_seconds', 'Request latency')

# Use in the agent
async def handle(self, question: str) -> tuple[str, str, list[str], dict]:
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        # Existing code
        result = await self.process_query(question)
    return result
```

2. **Structured logging**:

```python
import logging
import json

logger = logging.getLogger("sql_chat")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        if hasattr(record, 'session_id'):
            log_record["session_id"] = record.session_id
        if hasattr(record, 'question'):
            log_record["question"] = record.question
        if hasattr(record, 'sql'):
            log_record["sql"] = record.sql
        return json.dumps(log_record)

# Setup handler
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Usage in code
logger.info("Processing query", extra={"session_id": session_id, "question": question})
```

## 9. Advanced Development Topics

### 9.1 Context Window Management

When working with large schemas or complex conversations, manage the LLM context window effectively:

1. **Prioritize relevant schema information**:

```python
async def prioritize_tables(self, question: str, tables: list[str]) -> list[str]:
    # Use a lightweight LLM call to rank tables by relevance
    tables_text = "\n".join(tables)
    prompt = f"Question: {question}\nAvailable tables:\n{tables_text}\n\nRank these tables by relevance to the question, most relevant first. Return only a JSON array of table names."
    
    response = await call_llm(
        system_prompt="You are a helpful assistant that ranks database tables by relevance.",
        user_prompt=prompt,
        temperature=0.0
    )
    
    try:
        ranked_tables = json.loads(response)
        # Ensure all tables are included (even if not ranked)
        return ranked_tables + [t for t in tables if t not in ranked_tables]
    except:
        return tables
```

2. **Summarize conversation history**:

```python
def get_context_for_llm(self) -> str:
    """Get summarized conversation context for LLM"""
    if len(self.history) <= 3:
        # For short histories, include everything
        return self.get_full_context()
    else:
        # For longer histories, summarize older interactions
        recent = self.history[-3:]  # Keep last 3 interactions in full
        older = self.history[:-3]   # Summarize older interactions
        
        # Create the summary prompt
        history_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in older])
        summary_prompt = f"Summarize this conversation history concisely:\n{history_text}"
        
        # Get summary (synchronously for this example)
        loop = asyncio.new_event_loop()
        summary = loop.run_until_complete(call_llm(
            system_prompt="Summarize conversation history concisely, preserving key facts and context.",
            user_prompt=summary_prompt,
            temperature=0.3
        ))
        loop.close()
        
        # Combine summary with recent interactions
        recent_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in recent])
        return f"Conversation summary: {summary}\n\nRecent interactions:\n{recent_text}"
```

### 9.2 Error Handling and Fallbacks

Implement sophisticated error handling with smart fallbacks:

1. **SQL Error Correction with Multiple Attempts**:

```python
async def execute_with_fallbacks(self, sql: str, max_attempts: int = 3) -> Any:
    """Execute SQL with multiple correction attempts"""
    for attempt in range(max_attempts):
        try:
            result = await self.session.execute(text(sql))
            return result
        except Exception as e:
            error_msg = str(e)
            
            # Last attempt failed, give up
            if attempt == max_attempts - 1:
                raise
                
            # Try to correct the SQL
            sql = await self.correct_sql(sql, error_msg)
            
            # Log the correction attempt
            print(f"SQL Error: {error_msg}")
            print(f"Corrected SQL (attempt {attempt+1}): {sql}")
```

2. **Tiered LLM Model Fallback**:

```python
async def call_llm_with_fallback(system_prompt: str, user_prompt: str, temperature: float = 0.0):
    """Try calling primary LLM, fall back to backup models if needed"""
    try:
        # Try primary model first
        return await call_llm(system_prompt, user_prompt, temperature)
    except Exception as primary_error:
        print(f"Primary LLM error: {str(primary_error)}")
        try:
            # Fall back to secondary model
            return await call_secondary_llm(system_prompt, user_prompt, temperature)
        except Exception as secondary_error:
            print(f"Secondary LLM error: {str(secondary_error)}")
            # Final fallback to basic model
            return await call_basic_llm(system_prompt, user_prompt, temperature)
```

### 9.3 Advanced SQL Generation

Enhance SQL generation with specialized techniques:

1. **Two-stage SQL generation** for complex queries:

```python
async def generate_complex_sql(self, question: str, ddls: dict[str, str], context: str = "") -> str:
    """Generate SQL for complex questions using a two-stage approach"""
    # Stage 1: Generate a query plan
    plan_prompt = f"""
    Given this user question: "{question}"
    And these database table definitions:
    {json.dumps(ddls)}
    
    Create a step-by-step plan for constructing a SQL query:
    1. Which tables are needed?
    2. What joins will be required?
    3. What conditions should be applied?
    4. What aggregations or calculations are needed?
    5. How should results be ordered or limited?
    """
    
    query_plan = await call_llm(
        system_prompt="Create a detailed plan for constructing a SQL query.",
        user_prompt=plan_prompt,
        temperature=0.1
    )
    
    # Stage 2: Generate the SQL based on the plan
    sql_prompt = f"""
    Based on this query plan:
    {query_plan}
    
    Write a PostgreSQL query that answers the question: "{question}"
    The database has these table definitions:
    {json.dumps(ddls)}
    """
    
    sql = await call_llm(
        system_prompt="Generate a SQL query based on the provided plan.",
        user_prompt=sql_prompt,
        temperature=0.0
    )
    
    return sql
```

2. **Template-based generation** for common query patterns:

```python
def get_query_template(self, query_type: str) -> str:
    """Get a SQL template for common query patterns"""
    templates = {
        "count": "SELECT COUNT(*) FROM {table} WHERE {condition};",
        "top_n": "SELECT {columns} FROM {table} ORDER BY {order_column} DESC LIMIT {limit};",
        "time_series": "SELECT {time_column}, {agg_func}({value_column}) FROM {table} GROUP BY {time_column} ORDER BY {time_column};"
        # Add more templates as needed
    }
    return templates.get(query_type, "")

async def identify_query_pattern(self, question: str) -> str:
    """Identify the query pattern from a question"""
    pattern_prompt = f"""
    Categorize this question into one of these query patterns:
    - count: Questions about counting or "how many"
    - top_n: Questions about "top X" or "best X"
    - time_series: Questions about trends or changes over time
    - other: Any other query type
    
    Question: "{question}"
    
    Return only the pattern name (count, top_n, time_series, or other).
    """
    
    pattern = await call_llm(
        system_prompt="Categorize database questions into query patterns.",
        user_prompt=pattern_prompt,
        temperature=0.0
    )
    
    return pattern.strip().lower()
```

## 10. Custom Database Features Integration

### 10.1 Supporting PostgreSQL-Specific Features

Add support for advanced PostgreSQL features:

1. **Full-text search**:

```python
async def enhance_sql_with_full_text(self, sql: str, question: str) -> str:
    """Add full-text search capabilities to SQL queries when appropriate"""
    # Check if this is a search question
    search_terms = []
    search_prompt = f"Extract search terms from this question: '{question}'. Return only the search terms as a JSON array."
    
    search_terms_json = await call_llm(
        system_prompt="Extract search terms from questions.",
        user_prompt=search_prompt,
        temperature=0.0
    )
    
    try:
        search_terms = json.loads(search_terms_json)
    except:
        search_terms = []
    
    if not search_terms:
        return sql
    
    # Check if the query has WHERE clause
    if "WHERE" in sql.upper():
        # Add full-text search to existing WHERE clause
        search_condition = " AND (" + " OR ".join([f"to_tsvector('english', text_column) @@ to_tsquery('english', '{term}')" for term in search_terms]) + ")"
        sql = sql.replace("WHERE", "WHERE" + search_condition)
    else:
        # Add new WHERE clause with full-text search
        search_condition = " WHERE " + " OR ".join([f"to_tsvector('english', text_column) @@ to_tsquery('english', '{term}')" for term in search_terms])
        sql = sql.replace(";", search_condition + ";")
    
    return sql
```

2. **JSON data handling**:

```python
def enhance_ddl_with_json_paths(self, ddl: str) -> str:
    """Enhance DDL with JSON path information for JSON columns"""
    # Check if table has JSON columns
    if "json" not in ddl.lower() and "jsonb" not in ddl.lower():
        return ddl
    
    # Extract table name
    table_match = re.search(r"CREATE TABLE ([^\s]+)", ddl)
    if not table_match:
        return ddl
    
    table_name = table_match.group(1)
    
    # Look up JSON paths for this table
    json_paths = self.get_json_paths_for_table(table_name)
    if not json_paths:
        return ddl
    
    # Add JSON path information as comments
    json_info = "\n-- JSON Paths:\n"
    for column, paths in json_paths.items():
        json_info += f"-- Column: {column}\n"
        for path, description in paths.items():
            json_info += f"--   Path: {path} - {description}\n"
    
    # Add after the table comment but before the columns
    parts = ddl.split("\n", 1)
    if len(parts) > 1:
        return parts[0] + json_info + "\n" + parts[1]
    else:
        return ddl + json_info
```

### 10.2 Supporting Multi-Database Environments

Add support for querying multiple databases:

```python
class MultiDBSQLAgent:
    def __init__(self, sessions: Dict[str, AsyncSession], session_id: str = None):
        """SQL Agent for multiple databases"""
        self.sessions = sessions
        self.session_id = session_id or "default"
        self.memory = ConversationMemory(max_history=5)
    
    async def handle(self, question: str) -> tuple[str, str, list[str], dict]:
        """Process a question across multiple databases"""
        # First, determine which database is needed
        db_name = await self.determine_database(question)
        
        # Use the appropriate session
        if db_name in self.sessions:
            session = self.sessions[db_name]
            # Create a single-db agent and process
            agent = SQLAgent(session, self.session_id)
            return await agent.handle(question)
        else:
            # Default to the first database if not found
            default_db = next(iter(self.sessions.keys()))
            session = self.sessions[default_db]
            agent = SQLAgent(session, self.session_id)
            return await agent.handle(question)
    
    async def determine_database(self, question: str) -> str:
        """Determine which database should be used for this question"""
        # Get list of available databases
        db_list = list(self.sessions.keys())
        
        # Prompt the LLM to pick the most relevant database
        db_prompt = f"""
        Question: {question}
        Available databases: {', '.join(db_list)}
        
        Which database is most relevant for this question? Return only the database name.
        """
        
        response = await call_llm(
            system_prompt="Determine which database is most relevant for a given question.",
            user_prompt=db_prompt,
            temperature=0.0
        )
        
        # Return the selected database or the first one if not found
        selected_db = response.strip()
        return selected_db if selected_db in db_list else db_list[0]
```

## 11. Contribution Guidelines

### 11.1 Code Style

- Follow PEP 8 for Python code style
- Use type hints for all function parameters and return values
- Write docstrings for all classes and methods
- Use consistent variable naming conventions

### 11.2 Pull Request Process

1. Create a new branch for your feature or bugfix
2. Write tests for your changes
3. Ensure all tests pass
4. Submit a pull request with a clear description of the changes
5. Include any necessary documentation updates

### 11.3 Code Review Checklist

- Does the code follow our style guidelines?
- Are there appropriate tests?
- Is the documentation updated?
- Are there any security issues?
- Is the code efficient and maintainable?
- Are error cases handled properly?

## 12. Troubleshooting Guide

### 12.1 Common Issues and Solutions

1. **LLM API Errors**:
   - **Issue**: "Authentication error" or "Invalid API key"
   - **Solution**: Check that `OPENAI_API_KEY` and `LITELLM_AUTH_HEADER` are set correctly

2. **Database Connection Errors**:
   - **Issue**: "Could not connect to database"
   - **Solution**: Verify the `DATABASE_URL` and ensure the database is running
   - **Solution**: Check if the database driver is installed correctly

3. **Celery Worker Issues**:
   - **Issue**: Tasks stuck in "PENDING" state
   - **Solution**: Check if Celery workers are running using `docker-compose ps`
   - **Solution**: Check Celery logs with `docker-compose logs celery_worker`

4. **Redis Connection Issues**:
   - **Issue**: "Error connecting to Redis"
   - **Solution**: Verify Redis is running and accessible
   - **Solution**: Check Redis connection settings in `.env`

5. **Slow Query Performance**:
   - **Issue**: Queries taking too long to execute
   - **Solution**: Check for missing indexes in database
   - **Solution**: Review slow query logs
   - **Solution**: Adjust cache settings

### 12.2 Reading Logs

When troubleshooting, check the logs:

```bash
# API logs
docker-compose logs app

# Celery worker logs
docker-compose logs celery_worker

# Redis logs
docker-compose logs redis
```

### 12.3 Debugging Steps

1. **For SQL generation issues**:
   - Check the system and user prompts in `generate_sql` method
   - Test with simpler questions
   - Review the table schemas that are being provided to the LLM

2. **For LLM connection issues**:
   - Test the LLM connection directly
   - Check API keys and authentication
   - Verify network connectivity to the LLM service

3. **For database-related issues**:
   - Test database connectivity directly
   - Review schema definitions
   - Check table permissions

## 13. Future Development Roadmap

### 13.1 Planned Features

1. **Enhanced Security**:
   - Role-based access control
   - Query validation and security checks
   - Rate limiting and abuse prevention

2. **Advanced Visualization**:
   - Dynamic chart generation
   - Interactive visualizations
   - Dashboard creation capabilities

3. **Multi-Modal Support**:
   - File upload and analysis
   - Image and chart generation
   - Document-based question answering

4. **Advanced Context Management**:
   - Improved conversation memory
   - User preferences and defaults
   - Database metadata learning
