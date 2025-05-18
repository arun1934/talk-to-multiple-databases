# SQL DB Chat System Documentation

## 1. System Overview

The SQL DB Chat System is a natural language to SQL query application that allows users to ask questions in plain English and receive database results in a human-readable format. The system leverages large language models (LLMs) via LiteLLM to interpret user questions, generate appropriate SQL queries, execute them against a PostgreSQL database, and present the results in a user-friendly manner.

### Key Features

- Natural language to SQL translation
- Database query execution
- Human-readable results formatting
- Query caching for improved performance
- Conversation memory for contextual awareness
- Follow-up question suggestions
- Data visualization recommendations
- Asynchronous processing via Celery

## 2. System Architecture

The system follows a modern microservices architecture with the following components:

### 2.1 Core Components

- **FastAPI Backend**: Handles API requests and coordinates the workflow
- **SQL Agent**: Converts natural language to SQL and processes queries
- **LLM Integration**: Uses LiteLLM to connect to language models
- **Celery Worker**: Processes requests asynchronously
- **Redis**: Used for caching and as a message broker
- **PostgreSQL**: The database being queried

### 2.2 Architecture Diagram

```
+---------------+        +---------------+        +---------------+
|               |        |               |        |               |
|  FastAPI API  | -----> |  Celery Task  | -----> |   SQL Agent   |
|               |        |               |        |               |
+---------------+        +---------------+        +-------+-------+
        ^                                                |
        |                                                v
+-------+-------+                               +-------+-------+
|               |                               |               |
|  Redis Cache  | <--------------------------> | LiteLLM (LLM)  |
|               |                               |               |
+---------------+                               +---------------+
        ^                                                |
        |                                                v
        |                                       +-------+-------+
        |                                       |               |
        +-------------------------------------> |  PostgreSQL   |
                                                |               |
                                                +---------------+
```

## 3. Component Documentation

### 3.1 SQL Agent

The SQL Agent is the core component responsible for converting natural language queries to SQL, executing queries, and formatting results.

#### Flow Diagram

```
+---------------+        +---------------+        +---------------+
| Choose Tables | -----> |  Get Table    | -----> |  Generate SQL |
|               |        |  Definitions  |        |               |
+---------------+        +---------------+        +-------+-------+
                                                         |
+---------------+        +---------------+              v
|   Suggest     | <----- |   Format      | <----- | Execute SQL  |
| Follow-ups    |        |   Results     |        |              |
+---------------+        +---------------+        +--------------+
```

#### Components

1. **ConversationMemory**: Stores conversation history for context
2. **Table Selection**: Identifies which tables are relevant to the user's question
3. **DDL Generation**: Retrieves table definitions for context
4. **SQL Generation**: Creates SQL queries from natural language
5. **SQL Execution**: Runs queries against the database
6. **Results Formatting**: Converts SQL results to natural language
7. **Follow-up Suggestions**: Generates relevant follow-up questions

### 3.2 LLM Configuration

The LLM Configuration component manages the connection to the language model service through LiteLLM.

#### Key Features

- Centralized configuration for API endpoints and authentication
- Temperature control for different types of operations
- Standardized function for making LLM API calls
- Environment-based configuration

### 3.3 API Endpoints

The system exposes several RESTful API endpoints:

1. **POST /query**: Submit a natural language question
2. **GET /result/{task_id}**: Retrieve the results of a processed query
3. **POST /visualization-recommendation**: Get visualization suggestions for results

### 3.4 Caching System

The system implements a multi-level caching strategy:

1. **Query Cache**: Caches processed queries to avoid redundant processing
2. **DDL Cache**: Caches database table definitions
3. **Memory Cache**: Stores conversation history

## 4. Workflow Documentation

### 4.1 Query Processing Flow

```
+---------------+        +---------------+        +---------------+        +---------------+
|               |        |               |        |               |        |               |
| User Question | -----> | API Endpoint  | -----> | Celery Task   | -----> |  Check Cache  |
|               |        |               |        |               |        |               |
+---------------+        +---------------+        +---------------+        +-------+-------+
                                                                                   |
+---------------+        +---------------+        +---------------+                |
|               |        |               |        |               |                |
| Return Result | <----- | Format Result | <----- | Execute Query | <----- |  Not in Cache  |
|               |        |               |        |               |                |
+---------------+        +---------------+        +---------------+        +-------+-------+
                                                                                   |
                                                  +---------------+                |
                                                  |               |                |
                                                  |  Generate SQL | <----- | Get Table Info |
                                                  |               |                |
                                                  +---------------+        +---------------+
```

### 4.2 Visualization Recommendation Flow

```
+---------------+        +---------------+        +---------------+
|               |        |               |        |               |
| Query Results | -----> | LLM Analysis  | -----> | Visualization |
|               |        |               |        | Recommendation|
+---------------+        +---------------+        +---------------+
```

## 5. Developer Setup

### 5.1 Prerequisites

- Docker and Docker Compose
- Python 3.9+
- PostgreSQL database

### 5.2 Environment Setup

Create a `.env` file with the following variables:

```ini
# Database connection URL
DATABASE_URL=postgresql+asyncpg://postgres:admin@host.docker.internal/YourDB

# Redis URL for caching
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# OpenAI API key - using your LiteLLM key
OPENAI_API_KEY=your_api_key

# LiteLLM settings
LITELLM_API_BASE=https://lmlitellm.landmarkgroup.com
LITELLM_AUTH_HEADER=Bearer your_auth_header
LITELLM_MODEL=landmark-gpt-4o-mini

# LLM cache settings
ENABLE_LLM_CACHE=true
LLM_CACHE_TTL=300

# LLM temperature settings
GENERATION_TEMPERATURE=0.0
SUMMARY_TEMPERATURE=0.3
SUGGESTION_TEMPERATURE=0.5
```

### 5.3 Running the Application

1. Build the Docker containers:
   ```bash
   docker-compose build
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. Access the API at `http://localhost:8000`

### 5.4 Testing

To test the system, send a request to the query endpoint:

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "How many users do we have?", "session_id": "test-session"}'
```

Then retrieve the results:

```bash
curl "http://localhost:8000/result/{task_id}"
```

## 6. Configuration Options

### 6.1 LLM Settings

- **Model Selection**: Configure the model via `LITELLM_MODEL` environment variable
- **Temperature Control**: Set different temperatures for generation, summary, and suggestions
- **Caching**: Enable/disable caching via `ENABLE_LLM_CACHE`

### 6.2 Database Settings

- **Connection String**: Set via `DATABASE_URL` environment variable
- **Query Timeout**: Configure in the SQL Agent settings

### 6.3 Caching Settings

- **TTL**: Set cache expiration via `LLM_CACHE_TTL`
- **Redis Configuration**: Configure via Redis environment variables

## 7. Troubleshooting

### 7.1 Common Issues

1. **LLM API Errors**:
   - Check API key and authentication header
   - Verify the LiteLLM endpoint is accessible

2. **Database Connection Issues**:
   - Confirm database credentials
   - Check network connectivity to database

3. **Performance Issues**:
   - Review caching configuration
   - Check for slow database queries

### 7.2 Debugging

1. **Logging**:
   - Check application logs: `docker-compose logs app`
   - Check worker logs: `docker-compose logs celery_worker`

2. **API Testing**:
   - Use the FastAPI Swagger UI at `/docs`
   - Test individual endpoints for debugging

