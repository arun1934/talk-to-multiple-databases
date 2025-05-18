# SQL Chat Assistant: Complete Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [User Guide](#user-guide)
   - [Getting Started](#getting-started)
   - [Using the SQL Chat Assistant](#using-the-sql-chat-assistant)
   - [Managing Conversations](#managing-conversations)
   - [Tips for Effective Questions](#tips-for-effective-questions)
   - [Troubleshooting](#troubleshooting)
3. [Architecture Overview](#architecture-overview)
   - [System Overview](#system-overview)
   - [Component Architecture](#component-architecture)
   - [Data Flow](#data-flow)
   - [Scalability and Performance](#scalability-and-performance)
   - [Resilience and Error Handling](#resilience-and-error-handling)
   - [Security Considerations](#security-considerations)
4. [Developer Guide](#developer-guide)
   - [Technology Stack](#technology-stack)
   - [Project Structure](#project-structure)
   - [Core Components](#core-components)
   - [Development Workflow](#development-workflow)
   - [Extending the System](#extending-the-system)
   - [Common Development Issues](#common-development-issues)
   - [Best Practices](#best-practices)
5. [Docker Deployment Guide](#docker-deployment-guide)
   - [Prerequisites](#prerequisites)
   - [Quick Start](#quick-start)
   - [Advanced Configuration](#advanced-configuration)
   - [Health Checks and Monitoring](#health-checks-and-monitoring)
   - [Volume Management](#volume-management)
   - [Logging and Debugging](#logging-and-debugging)
   - [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
   - [Backup and Restore](#backup-and-restore)
6. [API Documentation](#api-documentation)
   - [Base URL](#base-url)
   - [API Endpoints](#api-endpoints)
   - [Client Implementation Guide](#client-implementation-guide)
   - [Error Handling](#error-handling)
   - [Rate Limiting](#rate-limiting)
   - [Performance Considerations](#performance-considerations)
7. [Product Requirements](#product-requirements)
   - [Problem Statement](#problem-statement)
   - [Target Users](#target-users)
   - [Product Overview](#product-overview)
   - [User Stories](#user-stories)
   - [Functional Requirements](#functional-requirements)
   - [Non-Functional Requirements](#non-functional-requirements)
   - [Technical Requirements](#technical-requirements)
   - [User Interface Requirements](#user-interface-requirements)
   - [Future Enhancements](#future-enhancements)
   - [Success Metrics](#success-metrics)
8. [Glossary](#glossary)

## Introduction

The NPS SQL Chat Assistant is a natural language interface for databases that allows users to query data using conversational language rather than writing SQL code. This system bridges the gap between business users and their data by translating natural language questions into SQL queries, executing them against databases, and presenting results in user-friendly formats with visualizations.

This comprehensive documentation combines user guides, technical architecture, development resources, deployment instructions, API references, and product requirements to serve as a complete resource for users, developers, administrators, and stakeholders.

## User Guide

### Getting Started

#### Accessing the Application

1. Open your web browser and navigate to the application URL provided by your administrator.
2. You'll be greeted with the NPS SQL Chat Assistant interface.

#### Interface Overview

The interface consists of the following elements:

- **Sidebar** (left): Displays your conversation history
- **Chat Area** (center): Shows the conversation between you and the AI assistant
- **Input Box** (bottom): Where you type your questions

User Interface: ![User Interface](Images/NPS-Chat-User-Interface.png)
: SQL Chat Assistant interface layout showing sidebar, chat area, and input box]

### Using the SQL Chat Assistant

#### Asking Questions

1. Type your question about the database in the input box at the bottom of the screen
2. Press Enter or click the send button (paper airplane icon)
3. The assistant will process your question and return a response

Example questions you can ask:
- "Tell me NPS based on the comments received last month"
- "Run a sentiment analysis on comments and summarize the themes"

#### Viewing Results

The assistant will provide:
- A natural language summary of the results
- A visualization of the data (when applicable)
- Suggestions for the follow up question

Example of SQL Chat Assistant results display showing summary, visualization, and SQL
![User Interface](Images/![User Interface](Images/Query-Execution.png)



#### Data Visualizations

When the assistant returns data that can be visualized:

1. Click the "📊 View Visualization" button below the response
2. The visualization will appear, showing your data in an appropriate chart format
3. You can download the data as CSV by clicking the "⬇️ Download CSV" button
![Visualization](Images/Visualization.png)


#### Follow-up Questions

After each response, the assistant may suggest follow-up questions related to your query. Simply click on one of these suggestions to ask the follow-up question.

### Managing Conversations

#### Starting a New Conversation

1. Click the "New Chat" button in the sidebar
2. This will start a fresh conversation with the assistant

#### Viewing Past Conversations

1. Your conversations are saved in the sidebar, organized by date
2. Click on any previous conversation to resume it

#### Managing Conversation History

For each conversation in the sidebar, you can:

- **Rename**: Click the three dots menu (...) and select "Rename chat"
- **Delete**: Click the three dots menu (...) and select "Delete chat"

#### Deleting Conversations

To delete conversation history:
1. Click the "Delete Session" button at the bottom of the sidebar
2. Confirm the deletion when prompted

### Tips for Effective Questions

To get the best results from the SQL Chat Assistant:

1. **Be specific**: Include the exact information you're looking for
   - Instead of "Show me NPS trend," try "Show me monthly NPS trend for 2025"

2. **Specify units and timeframes**: Clarify the units and time periods
   - "Show me NPR trend for Q1 2025"

3. **Mention tables or entities**: If you know which database tables contain your data, mention them
   - "Show me customer comment summary from the users table"

4. **Use business terminology**: You can use business terms rather than technical database terms

5. **Ask follow-ups**: Build on previous questions to explore your data further

### Troubleshooting

#### Common Issues

1. **Long Processing Times**: Complex queries may take longer to process. If a query takes too long, consider simplifying it.

2. **No Results**: If your query returns no results, try:
   - Broadening your criteria
   - Checking if you're using the correct entity names
   - Ensuring the data exists for the time period you specified

3. **Incorrect Interpretation**: If the assistant misunderstands your question:
   - Rephrase your question with more specific details
   - Break complex questions into smaller, simpler ones

#### Getting Help

If you encounter persistent issues, contact your system administrator or support team.

#### Privacy and Data Security

- The SQL Chat Assistant has access only to the databases configured by your administrator
- No sensitive data is sent to external services outside the organization's environment

## Architecture Overview

### System Overview

The SQL Chat Assistant follows a microservice-oriented architecture pattern with the following components:

h-level architecture diagram showing components and their relationships
![Architecture](Images/architecture-diagram.svg)

1. **Web Interface**: Frontend SPA for user interaction
2. **API Layer**: FastAPI application exposing endpoints
3. **Task Processing System**: Celery workers for asynchronous processing
4. **Database Connector**: Async SQLAlchemy for database interactions
5. **LLM Integration**: Language model integration for NL → SQL translation
6. **Caching System**: Redis for caching and as message broker
7. **Monitoring**: Prometheus and Grafana for observability

### Component Architecture

#### Web Interface

The frontend is a single-page application built with HTML, CSS, and JavaScript. Key features include:

- Real-time chat interface
- Local storage for conversation history using IndexedDB
- Data visualization with Chart.js
- Responsive design for mobile and desktop devices

#### API Layer

The API is built with FastAPI and provides the following endpoints:

- `/api/query`: Accepts natural language queries, routes to appropriate task queue
- `/api/result/{task_id}`: Returns results of asynchronous processing
- `/api/visualization-recommendation`: Provides chart recommendations based on data

#### Task Processing System

The task processing system uses Celery with multiple specialized workers:

- **Standard Query Worker**: Handles regular NL queries
- **Complex Query Worker**: Processes complex queries with longer timeouts
- **Simple Query Worker**: Handles simpler queries with shorter timeouts

Tasks are distributed based on query complexity and routed to the appropriate queue:

```
task_routes = {
    "process_nl_query": {"queue": "nl_tasks"},
    "process_complex_query": {"queue": "complex_tasks"},
    "process_simple_query": {"queue": "simple_tasks"}
}
```

#### SQLAgent Component

The core of the system is the `SQLAgent` class which implements the natural language to SQL workflow using LangGraph:

SQLAgent workflow showing the process flow from question to result
![Workfloe](Images/workflow-diagram.svg)
 

Each node in this workflow is implemented as an asynchronous function that processes and updates the state.


#### LLM Integration

The system integrates with language models through a centralized `call_llm` function:

- Handles API calls to the LLM provider
- Implements rate limiting, retries, and circuit breaking
- Provides consistent error handling

The LLM is used at multiple stages:
- Selecting relevant tables
- Generating SQL queries
- Formatting results in natural language
- Suggesting follow-up questions
- Recommending visualizations

#### Caching System

The caching system uses Redis and implements:

- A distributed cache for query results
- Session/conversation storage
- Message broker for Celery tasks
- Schema caching for database tables

#### Monitoring System

The monitoring system uses OpenTelemetry, Prometheus, and Grafana:

- Custom metrics for query processing times
- LLM call durations
- Cache hit/miss rates
- Error rates and types
- Active query counts

### Data Flow

#### Query Processing Flow

1. User submits a question through the web interface
2. The question is sent to the `/api/query` endpoint
3. The query complexity is classified
4. A Celery task is created in the appropriate queue
5. The task is picked up by a worker
6. The worker initializes an `SQLAgent` instance
7. The agent processes the query through the LangGraph workflow
8. Results are stored and made available via the `/api/result/{task_id}` endpoint
9. The frontend polls for results and displays them to the user


![Sequence](Images/Sequence-Diagram.png)

![Sequence](Images/Alternate-Flows.png)


#### Database Schema Handling

The system dynamically introspects database schemas:

1. The agent lists available tables using INFORMATION_SCHEMA
2. Relevant tables are selected based on the query
3. The agent fetches DDL (Data Definition Language) for the tables
4. DDL information is cached for future queries
5. Table structure is provided to the LLM for SQL generation

#### Conversation Context

Conversation context is maintained for better query understanding:

1. Previous questions, SQL queries, and results are stored in `ConversationMemory`
2. Context is included in prompts to the LLM
3. The context enables follow-up questions and references to previous queries

### Scalability and Performance

#### Horizontal Scaling

The system supports horizontal scaling through:

- Stateless API servers
- Multiple Celery workers with different specializations
- Worker replicas for parallel processing

From Docker Compose:
```yaml
celery_worker:
  deploy:
    replicas: 3

complex_worker:
  deploy:
    replicas: 2

simple_worker:
  deploy:
    replicas: 4
```

#### Performance Optimizations

Key performance optimizations include:

- **Multi-level caching**: Redis + in-memory caching
- **Schema caching**: Database schema information is cached
- **Connection pooling**: Database connections are pooled and reused
- **Query categorization**: Queries are routed to appropriate workers
- **Asynchronous processing**: Non-blocking I/O operations

#### Redis Configuration

Redis is configured for optimal performance:

```yaml
redis:
  command: redis-server --maxmemory 4gb --maxmemory-policy allkeys-lru
```

This configures:
- Maximum memory usage (4GB)
- LRU eviction policy (least recently used items are removed first)

### Resilience and Error Handling

#### Circuit Breaker

The system implements a circuit breaker pattern for LLM calls:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=30):
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.open_until = 0
```

This prevents cascading failures when the LLM service is unavailable.

#### Error Handling in SQL Generation

The system incorporates sophisticated error handling for SQL generation:

1. If SQL execution fails, the error is sent back to the LLM
2. The LLM attempts to correct the SQL based on the error message
3. If correction fails, a user-friendly error message is returned

#### Timeouts

Different timeout configurations are set for different query types:

```python
@celery_app.task(name="process_nl_query", soft_time_limit=60, time_limit=120)
def process_nl_query(query: str, session_id: str = None):
    # Regular queries

@celery_app.task(name="process_complex_query", soft_time_limit=180, time_limit=240)
def process_complex_query(query: str, session_id: str = None):
    # Complex queries

@celery_app.task(name="process_simple_query", soft_time_limit=30, time_limit=60)
def process_simple_query(query: str, session_id: str = None):
    # Simple queries
```

This ensures that no single query can consume too many resources.

### Security Considerations

#### SQL Injection Prevention

The system uses parameterized queries with SQLAlchemy to prevent SQL injection:

```python
result = await self.session.execute(text(sql))
```

Additionally, the LLM is instructed to generate safe SQL without direct user input interpolation.

#### Rate Limiting

Rate limiting is implemented for LLM API calls:

```python
class RateLimiter:
    def __init__(self, max_calls_per_minute=60):
        self.max_calls = max_calls_per_minute
        self.calls = 0
        self.lock = asyncio.Lock()
        self.reset_time = time.time() + 60
```

This prevents excessive API usage and associated costs.

#### Data Privacy

- Server-side caching uses non-identifiable hashes as keys
- No PII (Personally Identifiable Information) is logged in monitoring systems

## Developer Guide

### Technology Stack

The SQL Chat Assistant is built with the following technologies:

- **Backend**:
  - FastAPI - Web framework for API endpoints
  - SQLAlchemy - SQL toolkit and ORM
  - LangGraph - Framework for orchestrating LLM workflows
  - Celery - Distributed task queue
  - Redis - Message broker and caching
  - OpenTelemetry - Observability and metrics

- **Frontend**:
  - HTML/CSS/JavaScript - Client-side interface
  - Chart.js - Data visualization library
  - IndexedDB - Client-side storage

- **Deployment**:
  - Docker - Containerization
  - Docker Compose - Multi-container orchestration
  - Prometheus - Metrics collection
  - Grafana - Visualization dashboard

### Project Structure

```
.
├── app/
│   ├── agents/
│   │   └── sql_agent.py         # Core SQL translation logic
│   ├── cache/
│   │   ├── cache.py             # Redis connection initialization
│   │   └── redis_cache.py       # Redis caching utilities
│   ├── config/
│   │   ├── llm_config.py        # LLM configuration
│   │   └── settings.py          # Application settings
│   ├── memory/
│   │   └── conversation_memory.py  # Conversation history management
│   ├── routers/
│   │   └── agent.py             # API route definitions
│   ├── celery_app.py            # Celery configuration
│   ├── db.py                    # Database connection
│   ├── main.py                  # FastAPI app initialization
│   ├── monitoring.py            # Metrics and monitoring
│   └── tasks.py                 # Async task definitions
├── static/
│   ├── js/
│   │   ├── chart_utils.js       # Utilities for chart creation
│   │   └── visualizer.js        # Visualization logic
├── index.html                   # Main frontend interface
├── check_port.py                # Utility for checking port availability
├── docker-compose.yml           # Container orchestration
├── prometheus.yml               # Prometheus configuration
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

### Core Components

#### 1. SQL Agent

The `SQLAgent` class in `sql_agent.py` is the core component that processes natural language queries:

```python
class SQLAgent:
    def __init__(self, session: AsyncSession, session_id: str = None):
        self.session = session
        self.session_id = session_id or "default"
        self.memory = ConversationMemory(max_history=5)
```

Key methods include:
- `handle()`: Main entry point for processing queries
- `choose_tables()`: Selects relevant tables for a query
- `generate_sql()`: Creates SQL from natural language
- `execute_sql()`: Runs the generated SQL
- `format_results_as_natural_language()`: Converts results to readable text

#### 2. LangGraph Workflow

The query processing uses LangGraph to orchestrate a step-by-step workflow:

```python
# Define state type
class GraphState(TypedDict):
    question: str
    context: str
    tables: tuple[str, ...] | None
    ddls: dict[str, str] | None
    sql: str
    result: str
    formatted_result: str
    suggestions: list[str]
    table: dict

# Create graph
graph = StateGraph(GraphState)

# Add nodes for each step
graph.add_node('choose_tables', choose_tables_node)
graph.add_node('get_ddls', get_ddls_node)
graph.add_node('generate_sql', generate_sql_node)
graph.add_node('execute_sql', execute_sql_node)
graph.add_node('suggest_followups', suggest_followups_node)

# Define edges
graph.add_edge(START, 'choose_tables')
graph.add_edge('choose_tables', 'get_ddls')
# ...
```

#### 3. FastAPI Routes

API endpoints are defined in `agent.py`:

```python
@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    # Process query and return task ID
    
@router.get("/result/{task_id}")
async def get_result(task_id: str):
    # Retrieve results for a specific task
    
@router.post("/visualization-recommendation", response_model=VisualizationResponse)
async def get_visualization_recommendation(request: VisualizationRequest):
    # Get visualization recommendations
```

#### 4. Celery Tasks

Asynchronous task processing is handled by Celery in `tasks.py`:

```python
@celery_app.task(name="process_nl_query", soft_time_limit=60, time_limit=120)
def process_nl_query(query: str, session_id: str = None):
    """Process regular complexity queries"""
    
@celery_app.task(name="process_complex_query", soft_time_limit=180, time_limit=240)
def process_complex_query(query: str, session_id: str = None):
    """Process complex queries with longer timeout"""
```

#### 5. Frontend Implementation

The frontend is a single-page application with these key components:

- Chat interface (`index.html`)
- Session management using IndexedDB
- Data visualization with Chart.js
- Responsive design for mobile and desktop

### Development Workflow

#### Setting Up the Development Environment

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file
4. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

#### Adding New Features

##### Backend Modifications

1. To add a new API endpoint:
   - Add route in `app/routers/agent.py`
   - Define request/response models
   - Implement business logic

2. To modify SQL generation:
   - Update LLM prompts in `sql_agent.py`
   - Enhance the workflow in LangGraph nodes

3. To add monitoring metrics:
   - Add metrics in `app/monitoring.py`
   - Instrument relevant code points

##### Frontend Modifications

1. To update the UI:
   - Modify HTML/CSS in `index.html`
   - Update JavaScript functions for user interactions

2. To enhance visualizations:
   - Edit visualization logic in `visualizer.js`
   - Add or modify chart types in Chart.js integration

#### Testing

1. Manual testing:
   - Use the web interface to test end-to-end functionality
   - Check different types of queries (simple, complex)
   - Verify visualization outputs
   
2. API testing:
   - Use tools like Postman or curl to test API endpoints

3. Component testing:
   - Test individual functions with unit tests
   - Verify LLM outputs for different queries

#### Debugging

1. Backend issues:
   - Check application logs
   - Use the debugging endpoints
   - Monitor Prometheus metrics

2. Frontend issues:
   - Use browser developer tools
   - Check console for errors
   - Verify network requests/responses

### Extending the System

#### Adding New Database Support

To add support for a new database type:

1. Update the SQLAlchemy engine configuration in `app/db.py`
2. Modify the `get_ddls` method in `SQLAgent` to support the new dialect
3. Adjust SQL generation prompts for compatible syntax

#### Enhancing LLM Integration

To upgrade or change the LLM backend:

1. Update `app/config/llm_config.py` with new model parameters
2. Adjust prompts in `sql_agent.py` for the new model
3. Test thoroughly with various query types

#### Adding Custom Visualizations

To add new visualization types:

1. Create new chart creation functions in `visualizer.js`
2. Update the visualization recommendation logic
3. Add new chart rendering in the frontend

### Common Development Issues

#### LLM Response Parsing

Problem: Inconsistent LLM responses causing JSON parsing errors
Solution: Implement robust parsing with multiple fallback strategies

```python
# Example from the code
try:
    # Try direct JSON parsing first
    if response.strip().startswith("[") and response.strip().endswith("]"):
        chosen = json.loads(response)
        # ...
    # Look for table names directly in the response
    found_tables = []
    for table in tables:
        if table in response:
            found_tables.append(table)
    # ...
except Exception as e:
    # Fallback strategy
```

#### Celery Task Timeouts

Problem: Long-running tasks being terminated
Solution: Adjust timeouts and implement task chunking

```python
@celery_app.task(name="process_complex_query", soft_time_limit=180, time_limit=240)
def process_complex_query(query: str, session_id: str = None):
    try:
        # Process query
    except SoftTimeLimitExceeded:
        # Handle timeout gracefully
```

#### Database Connection Issues

Problem: Connection pool exhaustion
Solution: Properly configure connection pooling and implement connection recycling

```python
engine = create_async_engine(
    settings.db_url,
    pool_size=getattr(settings, 'db_pool_size', 20),
    max_overflow=getattr(settings, 'db_max_overflow', 30),
    pool_timeout=getattr(settings, 'db_pool_timeout', 30),
    pool_recycle=getattr(settings, 'db_pool_recycle', 300),
    pool_pre_ping=True
)
```

### Best Practices

1. **Error Handling**: Always implement proper error handling with fallbacks
2. **Circuit Breaking**: Use circuit breakers for external services
3. **Caching**: Cache expensive operations and results
4. **Monitoring**: Add metrics for critical components
5. **Async Operations**: Use async/await for I/O-bound operations
6. **Documentation**: Keep code comments and documentation up-to-date
7. **Testing**: Test with various input types and edge cases

## Docker Deployment Guide

### Prerequisites

Before proceeding, ensure you have the following installed:

- Docker Engine (version 20.10.0 or higher)
- Docker Compose (version 2.0.0 or higher)
- Git (for cloning the repository)

You should also have:
- Access to a PostgreSQL or compatible database
- At least 8GB of RAM available for containers
- 20GB of free disk space

### System Architecture

The SQL Chat Assistant consists of the following Docker containers:

- **app**: FastAPI web application
- **celery_worker**: Standard query processing worker
- **complex_worker**: Worker for complex queries
- **simple_worker**: Worker for simple queries
- **redis**: Cache and message broker
- **flower**: Celery task monitoring
- **prometheus**: Metrics collection
- **grafana**: Metrics visualization

### Quick Start

#### 1. Clone the Repository

```bash
git clone <Repository Path>
cd sql-chat-assistant
```

#### 2. Configure Environment Variables

Create an `.env` file in the `app` directory:

```bash
# Create .env file
touch app/.env
```

Add the following environment variables to the `.env` file:

```
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=300

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# LLM Configuration
LITELLM_API_BASE=https://your-llm-api-endpoint.com
LITELLM_MODEL=gpt-4.1-mini
LITELLM_AUTH_HEADER=your-auth-header
OPENAI_API_KEY=your-openai-api-key

# Caching and Performance
ENABLE_LLM_CACHE=true
LLM_CACHE_TTL=300
GENERATION_TEMPERATURE=0.0
SUMMARY_TEMPERATURE=0.3
SUGGESTION_TEMPERATURE=0.5

# Scaling and Performance Settings
USE_REDIS_CLUSTER=false
LLM_RATE_LIMIT=60
LLM_FAILURE_THRESHOLD=5
LLM_RESET_TIMEOUT=30
```

#### 3. Build and Start the Containers

```bash
docker-compose up -d
```

This command will:
- Build the Docker images if they don't exist
- Create and start all the containers defined in `docker-compose.yml`
- Set up the necessary networks and volumes

#### 4. Verify Deployment

Check if all containers are running:

```bash
docker-compose ps
```

You should see all services with status "Up":

```
    Name                   Command               State           Ports
-------------------------------------------------------------------------------
app                python -m uvicorn main:app ... Up      0.0.0.0:8000->8000/tcp
celery_worker     celery -A celery_app worker ... Up
complex_worker    celery -A celery_app worker ... Up
simple_worker     celery -A celery_app worker ... Up
redis             redis-server --maxmemory 4... Up      0.0.0.0:6379->6379/tcp
flower            flower --port=5555 --broker... Up      0.0.0.0:5555->5555/tcp
prometheus        /bin/prometheus --config.f... Up      0.0.0.0:9090->9090/tcp
grafana           /run.sh                         Up      0.0.0.0:3000->3000/tcp
```

#### 5. Access the Application

- Web UI: http://localhost:8000
- Flower (Celery monitoring): http://localhost:5555
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (default credentials: admin/admin)

### Advanced Configuration

#### Container Resources

By default, the Docker Compose file does not specify resource limits. For production deployments, add resource constraints to each service:

```yaml
services:
  app:
    # ... existing configuration
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

#### Worker Scaling

To adjust the number of worker instances, modify the `replicas` parameter in the Docker Compose file:

```yaml
services:
  celery_worker:
    # ... existing configuration
    deploy:
      replicas: 3  # Change this number to scale up/down

  complex_worker:
    # ... existing configuration
    deploy:
      replicas: 2  # Change this number to scale up/down

  simple_worker:
    # ... existing configuration
    deploy:
      replicas: 4  # Change this number to scale up/down
```

After changing these values, run:

```bash
docker-compose up -d --scale celery_worker=3 --scale complex_worker=2 --scale simple_worker=4
```

#### Redis Configuration

Redis is configured with memory limits and an LRU eviction policy. To adjust these settings, modify the Redis command in the Docker Compose file:

```yaml
services:
  redis:
    # ... existing configuration
    command: redis-server --maxmemory 4gb --maxmemory-policy allkeys-lru
```

For higher memory environments, increase the maxmemory value.

#### Prometheus Configuration

The Prometheus configuration is located in `prometheus.yml`. You can modify scrape intervals and targets:

```yaml
global:
  scrape_interval: 15s     # Adjust how frequently to collect metrics
  evaluation_interval: 15s # Adjust how frequently to evaluate rules

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'app'
    scrape_interval: 5s    # More frequent scraping for the app
    static_configs:
      - targets: ['app:8000']
```

### Health Checks and Monitoring

#### Using Health Check Endpoints

The application provides a health check endpoint that you can use to monitor the system:

```bash
curl http://localhost:8000/health
```

This returns a JSON response with the status of various components:

```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "api": "running"
  }
}
```

#### Monitoring with Grafana

1. Access Grafana at http://localhost:3000
2. Log in with default credentials (admin/admin)
3. Add Prometheus as a data source:
   - Go to Configuration > Data Sources
   - Add Prometheus data source
   - Set URL to `http://prometheus:9090`
   - Click "Save & Test"
4. Import dashboards:
   - Go to Dashboard > Import
   - Upload dashboard JSON files or enter dashboard IDs

Some useful metrics to monitor:
- Query duration
- SQL execution time
- LLM API call duration
- Cache hit/miss rates
- Active query count
- Error rates

### Volume Management

The Docker Compose file defines the following volumes for persistence:

```yaml
volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

These volumes persist data even when containers are restarted or recreated.

To view the volumes:

```bash
docker volume ls
```

To backup a volume:

```bash
docker run --rm -v sql-chat-assistant_redis_data:/source -v $(pwd):/backup alpine tar -czvf /backup/redis-backup.tar.gz /source
```

To restore from a backup:

```bash
docker run --rm -v sql-chat-assistant_redis_data:/target -v $(pwd):/backup alpine sh -c "rm -rf /target/* && tar -xzvf /backup/redis-backup.tar.gz -C /target"
```

### Logging and Debugging

#### Viewing Logs

To view logs for all containers:

```bash
docker-compose logs
```

To view logs for a specific service:

```bash
docker-compose logs app
```

To follow logs in real-time:

```bash
docker-compose logs -f app
```

#### Debugging a Container

To access a running container for debugging:

```bash
docker-compose exec app bash
```

This gives you a shell inside the container where you can examine files, run commands, etc.

### Common Issues and Troubleshooting

#### Port Conflicts

If you see errors like "port is already allocated," you may have a port conflict:

1. Check what's using the port:
   ```bash
   lsof -i :8000
   ```

2. Either stop the conflicting application or modify the port mapping in `docker-compose.yml`:
   ```yaml
   ports:
     - "8001:8000"  # Now the app will be available on port 8001
   ```

#### Container Not Starting

If a container fails to start:

1. Check the logs:
   ```bash
   docker-compose logs <service_name>
   ```

2. Verify environment variables:
   ```bash
   docker-compose config
   ```

3. Check if volumes have proper permissions:
   ```bash
   docker volume inspect sql-chat-assistant_redis_data
   ```

#### Database Connection Issues

If the application can't connect to the database:

1. Verify your `DATABASE_URL` in the `.env` file
2. Ensure the database is accessible from the container network
3. Check if the database credentials are correct
4. Try connecting to the database from the app container:
   ```bash
   docker-compose exec app python -c "import asyncio, asyncpg; asyncio.run(asyncpg.connect('your_connection_string'))"
   ```

#### LLM API Issues

If the application can't connect to the LLM API:

1. Check your API credentials in `.env`
2. Verify the API endpoint is accessible
3. Look for rate limiting or authorization errors in the logs
4. Test the API connection from the container:
   ```bash
   docker-compose exec app curl -v <your_llm_api_endpoint>
   ```

### Backup and Restore

#### Backing Up the Application

1. Back up the environment variables:
   ```bash
   cp app/.env .env.backup
   ```

2. Back up volumes:
   ```bash
   docker run --rm -v sql-chat-assistant_redis_data:/source -v $(pwd):/backup alpine tar -czvf /backup/redis-backup.tar.gz /source
   docker run --rm -v sql-chat-assistant_prometheus_data:/source -v $(pwd):/backup alpine tar -czvf /backup/prometheus-backup.tar.gz /source
   docker run --rm -v sql-chat-assistant_grafana_data:/source -v $(pwd):/backup alpine tar -czvf /backup/grafana-backup.tar.gz /source
   ```

3. Back up your database separately using appropriate tools for your database system

#### Restoring the Application

1. Restore environment variables:
   ```bash
   cp .env.backup app/.env
   ```

2. Restore volumes:
   ```bash
   docker run --rm -v sql-chat-assistant_redis_data:/target -v $(pwd):/backup alpine sh -c "rm -rf /target/* && tar -xzvf /backup/redis-backup.tar.gz -C /"
   docker run --rm -v sql-chat-assistant_prometheus_data:/target -v $(pwd):/backup alpine sh -c "rm -rf /target/* && tar -xzvf /backup/prometheus-backup.tar.gz -C /"
   docker run --rm -v sql-chat-assistant_grafana_data:/target -v $(pwd):/backup alpine sh -c "rm -rf /target/* && tar -xzvf /backup/grafana-backup.tar.gz -C /"
   ```

3. Start the containers:
   ```bash
   docker-compose up -d
   ```

## API Documentation

### Base URL

```
https://<deployment-url>/api
```

For local development:

```
http://localhost:8000/api
```

### API Endpoints

#### Query Endpoint

Submits a natural language question for processing.

**Endpoint:** `POST /query`

**Request Format:**

```json
{
  "question": "How many comments received last month?",
  "session_id": "optional-session-identifier"
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| question | string | Yes | The natural language question to process |
| session_id | string | No | Optional session identifier for maintaining conversation context |

**Response Format:**

```json
{
  "task_id": "c7f3943e-7b8d-4ae7-ab3f-c7b348a45a3b"
}
```

| Field | Type | Description |
|-------|------|-------------|
| task_id | string | Unique identifier for the created task |

**Status Codes:**

- 200: Query submitted successfully
- 400: Invalid request
- 500: Server error

**Example:**

```bash
curl -X POST https://deployment-url/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many comments received last month?", "session_id": "user123"}'
```

#### Result Endpoint

Retrieves the result of a previously submitted query.

**Endpoint:** `GET /result/{task_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| task_id | string | The unique task identifier returned by the query endpoint |

**Response Format:**

*Processing:*
```json
{
  "status": "processing"
}
```

*Completed:*
```json
{
  "status": "completed",
  "result": {
    "sql": "SELECT ...",
    "result": "Based on the query results, 1,245 users registered last month.",
    "formatted_result": "There were 1,245 new comments received last month.",
    "suggestions": [
      "How does this compare to the previous month?",
      "What's the breakdown of comments by categories?",
      "How many of these users have given positive comments?"
    ],
    "table": {
      "columns": ["count"],
      "rows": [[1245]]
    }
  }
}
```

*Failed:*
```json
{
  "status": "failed",
  "error": "Error executing query: table 'users' does not exist"
}
```

| Field | Type | Description |
|-------|------|-------------|
| status | string | Current status of the task: "processing", "completed", or "failed" |
| result | object | Present only for completed tasks |
| result.sql | string | Generated SQL query |
| result.result | string | Raw result text |
| result.formatted_result | string | User-friendly formatted results |
| result.suggestions | array | Follow-up question suggestions |
| result.table | object | Table structure with columns and rows |
| error | string | Error message (only for failed tasks) |

**Status Codes:**

- 200: Request successful (regardless of task status)
- 404: Task not found
- 500: Server error

**Example:**

```bash
curl -X GET https://your-deployment-url/api/result/c7f3943e-7b8d-4ae7-ab3f-c7b348a45a3b
```

#### Visualization Recommendation Endpoint

Recommends appropriate visualization types for query results.

**Endpoint:** `POST /visualization-recommendation`

**Request Format:**

```json
{
  "question": "How many comments received in 2025?",
  "sqlQuery": "SELECT DATE_TRUNC('month', nps_date) AS month, COUNT(*) AS count FROM users WHERE EXTRACT(YEAR FROM registration_date) = 2023 GROUP BY month ORDER BY month",
  "results": "month | count\n2023-01-01 | 1240\n2023-02-01 | 1582\n2023-03-01 | 1790\n..."
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| question | string | Yes | The original natural language question |
| sqlQuery | string | Yes | The SQL query that was executed |
| results | string | Yes | String representation of the query results |

**Response Format:**

```json
{
  "visualization": "line",
  "visualization_reason": "Line chart is recommended for showing trends over time. The query analyzes user registrations across months, which is time-series data best displayed as a line chart to visualize the trend."
}
```

| Field | Type | Description |
|-------|------|-------------|
| visualization | string | Recommended visualization type: "bar", "line", "pie", "horizontal_bar", "scatter", or "none" |
| visualization_reason | string | Explanation for the recommendation |

**Status Codes:**

- 200: Recommendation provided successfully
- 400: Invalid request
- 500: Server error

**Example:**

```bash
curl -X POST https://your-deployment-url/api/visualization-recommendation \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many comments received in 2025?",
    "sqlQuery": "SELECT DATE_TRUNC('month', registration_date) AS month, COUNT(*) AS count FROM users WHERE EXTRACT(YEAR FROM registration_date) = 2023 GROUP BY month ORDER BY month",
    "results": "month | count\n2023-01-01 | 1240\n2023-02-01 | 1582\n2023-03-01 | 1790\n..."
  }'
```

#### Health Check Endpoint

Checks the health of the application and its dependencies.

**Endpoint:** `GET /health`

**Response Format:**

*Healthy:*
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "api": "running"
  }
}
```

*Unhealthy:*
```json
{
  "status": "unhealthy",
  "services": {
    "database": "disconnected",
    "redis": "connected",
    "api": "running"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| status | string | Overall system status: "healthy" or "unhealthy" |
| services | object | Status of individual components |
| services.database | string | Database connection status |
| services.redis | string | Redis connection status |
| services.api | string | API service status |

**Status Codes:**

- 200: System is healthy
- 503: System is unhealthy
- 500: Error checking health

**Example:**

```bash
curl -X GET https://your-deployment-url/health
```

#### Metrics Endpoint

Exposes Prometheus metrics for monitoring.

**Endpoint:** `GET /metrics`

**Response Format:** Prometheus-compatible metrics output

**Example:**

```bash
curl -X GET https://your-deployment-url/metrics
```

### Client Implementation Guide

#### Basic Query Flow

1. **Submit a question**:
   - Make a POST request to `/api/query`
   - Store the returned `task_id`

2. **Poll for results**:
   - Make GET requests to `/api/result/{task_id}` periodically
   - Continue polling until status is not "processing"
   - Recommended polling interval: 1 second

3. **Handle the response**:
   - If status is "completed", display the formatted results and table data
   - If status is "failed", display the error message

#### Example Implementation (JavaScript)

```javascript
async function queryDatabase(question, sessionId = null) {
  try {
    // Step 1: Submit the question
    const queryResponse = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question,
        session_id: sessionId
      })
    });
    
    const { task_id } = await queryResponse.json();
    
    // Step 2: Poll for results
    let result;
    let isProcessing = true;
    
    while (isProcessing) {
      const resultResponse = await fetch(`/api/result/${task_id}`);
      result = await resultResponse.json();
      
      if (result.status !== "processing") {
        isProcessing = false;
      } else {
        // Wait before trying again
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    // Step 3: Handle the response
    if (result.status === "completed") {
      return {
        success: true,
        data: result.result
      };
    } else {
      return {
        success: false,
        error: result.error
      };
    }
  } catch (error) {
    return {
      success: false,
      error: `Error: ${error.message}`
    };
  }
}

async function getVisualizationRecommendation(question, sqlQuery, results) {
  try {
    const response = await fetch('/api/visualization-recommendation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question,
        sqlQuery: sqlQuery,
        results: results
      })
    });
    
    return await response.json();
  } catch (error) {
    console.error("Error getting visualization recommendation:", error);
    return { visualization: "none" };
  }
}
```

### Error Handling

The API uses standard HTTP status codes and includes detailed error messages in the response body:

#### Common Error Responses

**Bad Request (400)**:
```json
{
  "detail": "Invalid request format. Check your request parameters."
}
```

**Not Found (404)**:
```json
{
  "detail": "Task with ID 'invalid-id' not found."
}
```

**Internal Server Error (500)**:
```json
{
  "detail": "An unexpected error occurred while processing your request."
}
```

### Rate Limiting

The API implements rate limiting to ensure fair usage:

- Maximum of 60 requests per minute per client IP
- Exceeded rate limits return 429 Too Many Requests status
- The response includes headers with rate limit information:
  - `X-RateLimit-Limit`: Maximum requests per minute
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time in seconds until the rate limit resets

### Performance Considerations

- **Long-running queries**: Some complex queries may take longer to process. Implement appropriate timeouts in your client.
- **Result caching**: Results are cached for 5 minutes by default. Identical questions will return results faster.
- **Connection pooling**: The API manages database connections efficiently, but clients should close HTTP connections when done.

## Product Requirements

### Problem Statement

#### Background

Organizations collect and store vast amounts of data in relational databases, but accessing this data traditionally requires:
- SQL knowledge, which many business users lack
- Time-consuming query development
- Technical assistance from data teams, creating bottlenecks
- Specialized tools that may be difficult to use

#### Problems to Solve

1. **Technical Barrier**: Business users without SQL knowledge cannot directly access data they need.
2. **Productivity Loss**: Data analysts spend significant time writing queries for others rather than performing complex analysis.
3. **Insight Delay**: Business decisions are delayed waiting for data access.
4. **Learning Curve**: Training users on SQL and database schemas requires significant investment.
5. **Query Iteration**: Developing the right query often requires multiple attempts, consuming valuable time.

### Target Users

#### Primary Users

1. **Business Analysts**
   - Need data for reporting and decision-making
   - Have domain knowledge but limited SQL skills
   - Use data frequently but don't want to learn complex query language

2. **Data-Driven Decision Makers**
   - Executives, managers, and team leads
   - Need quick access to business metrics
   - Don't have time to learn technical skills for data access

3. **Product Managers**
   - Need to understand product usage and metrics
   - Require data for product decisions
   - Want self-service access to data without engineer dependency

#### Secondary Users

1. **Data Engineers & Analysts**
   - Can use the tool for quick data checks
   - Use it to create reusable queries for others
   - Monitor data quality and patterns

2. **Software Developers**
   - Need to understand application data behaviors
   - Investigate bugs or performance issues
   - Prototype data-based features

#### User Needs Assessment

| User Group | Primary Needs | Current Pain Points | Success Criteria |
|------------|---------------|---------------------|------------------|
| Business Analysts | Self-service data access, ability to explore data | Dependency on data team, SQL knowledge gap | 80% of routine queries self-serviced |
| Decision Makers | Quick insights, real-time data visualization | Delayed access to data, inability to drill down | Reduction in time-to-insight by 70% |
| Product Managers | Product metrics, user behavior insights | Engineering team bottlenecks | Increased frequency of data-driven decisions |
| Data Engineers | Efficiency tools, delegation of routine queries | Time spent on basic queries for others | 50% reduction in routine query requests |
| Developers | Database debugging, data validation | Context switching to DB tools | Faster debugging cycles |

### Product Overview

#### Product Vision

The SQL Chat Assistant will democratize data access within organizations by enabling anyone to query databases through natural language conversations. It will bridge the technical gap between business users and their data, accelerating decision-making and reducing the workload on data teams.

#### Key Value Propositions

1. **Accessibility**: Make database querying accessible to non-technical users
2. **Efficiency**: Reduce time spent constructing SQL queries
3. **Self-Service**: Empower users to get answers without technical help
4. **Learning**: Help users gradually understand their data structures
5. **Visualization**: Automatically visualize data in appropriate formats

#### Product Scope

The SQL Chat Assistant will provide:

1. A web-based conversational interface for natural language database queries
2. Translation of natural language to SQL with verification
3. Execution of SQL against connected databases
4. Natural language summaries of query results
5. Automatic data visualization
6. Conversation history and context management
7. Follow-up question suggestions

#### Product Constraints

1. Limited to supported SQL-compatible databases
2. Requires proper database schema setup and access
3. Not intended to replace comprehensive BI tools for complex reporting
4. May not handle extremely complex or multi-part queries optimally

### User Stories

#### Business Analyst

1. As a business analyst, I want to query our customer database in plain English so that I can quickly find metrics without writing SQL.
2. As a business analyst, I want to see visualizations of my query results so that I can identify patterns more easily.
3. As a business analyst, I want to refine my questions through follow-ups so that I can drill down into interesting data points.
4. As a business analyst, I want to access my previous queries so that I can reuse effective questions.

#### Decision Maker

1. As a manager, I want to ask simple questions about our KPIs so that I can make informed decisions without requesting reports.
2. As an executive, I want to see visual representations of data so that I can quickly understand trends.
3. As a team lead, I want to compare current metrics to previous periods so that I can track progress against goals.
4. As a department head, I want to access data on my own schedule so that I'm not bottlenecked by the data team's availability.

#### Data Engineer

1. As a data engineer, I want to direct non-technical colleagues to the SQL Chat Assistant so that I can focus on complex data problems.
2. As a data engineer, I want to see what SQL is being generated so that I can verify correctness and optimize our schemas.
3. As a data engineer, I want users to have access to data without compromising security so that we maintain proper data governance.

#### Developer

1. As a developer, I want to quickly query production data to debug issues so that I can resolve problems faster.
2. As a developer, I want to understand data relationships through conversational queries so that I can better design features.

### Functional Requirements

#### Natural Language Query Processing

1. The system shall accept natural language questions about database content.
2. The system shall support various question phrasings and synonyms for database entities.
3. The system shall maintain conversation context to enable follow-up questions.
4. The system shall clarify ambiguous questions by asking for specific details.
5. The system shall suggest related follow-up questions based on query results.

#### SQL Generation and Execution

1. The system shall translate natural language queries into correct SQL statements.
2. The system shall display the generated SQL query to the user.
3. The system shall execute the generated SQL against the connected database.
4. The system shall handle errors in SQL execution and attempt correction.
5. The system shall optimize queries for performance where possible.

#### Result Presentation

1. The system shall provide natural language summaries of query results.
2. The system shall display tabular results when appropriate.
3. The system shall automatically select and generate appropriate visualizations.
4. The system shall provide options to download results in common formats (CSV).

#### Conversation Management

1. The system shall maintain conversation history for each user session.
2. The system shall allow users to view and return to previous conversations.
3. The system shall enable users to rename and organize their conversations.
4. The system shall allow users to delete conversations when no longer needed.

#### Visualization

1. The system shall automatically recommend appropriate chart types for query results.
2. The system shall support multiple visualization types: bar, line, pie, scatter, and horizontal bar charts.
3. The system shall style visualizations with accessible color schemes.
4. The system shall allow users to download visualizations.

### Non-Functional Requirements

#### Performance

1. The system shall process simple queries within 5 seconds.
2. The system shall process complex queries within 30 seconds.
3. The system shall support at least 100 concurrent users.
4. The system shall cache query results for improved response times.
5. The system shall implement timeouts for long-running queries.

#### Reliability

1. The system shall have 99.9% uptime during business hours.
2. The system shall gracefully handle database connection failures.
3. The system shall provide appropriate error messages for system issues.
4. The system shall implement circuit breakers for external service dependencies.

#### Security

1. The system shall authenticate users via Microsoft login before granting database access.
2. The system shall enforce database-level permissions for each user.
3. The system shall not expose sensitive database schema details.
4. The system shall log all queries for audit purposes.
5. The system shall implement rate limiting to prevent abuse.

#### Usability

1. The system shall provide an intuitive chat interface requiring minimal training.
2. The system shall support keyboard navigation for accessibility.
3. The system shall be responsive on desktop and tablet devices.
4. The system shall conform to WCAG 2.1 AA accessibility standards.
5. The system shall provide clear feedback during processing.

#### Scalability

1. The system shall scale horizontally to handle increased user load.
2. The system shall support multiple database connections.
3. The system shall dynamically allocate resources based on query complexity.

### Technical Requirements

#### Supported Databases

1. The system shall support PostgreSQL databases.
2. The system shall support connection to multiple databases simultaneously.
3. The system shall support future expansion to other SQL-compatible databases.

#### Integration Points

1. The system shall provide a REST API for integration with other systems.
2. The system shall support authentication via OAuth 2.0.
3. The system shall provide webhook capabilities for query completion events.

#### Deployment

1. The system shall be deployable via Docker containers.
2. The system shall support horizontal scaling of worker processes.
3. The system shall include monitoring endpoints for health checks.
4. The system shall export metrics in Prometheus format.

#### Caching

1. The system shall cache query results to improve performance.
2. The system shall cache database schema information.
3. The system shall implement an LRU (Least Recently Used) cache eviction policy.
4. The system shall allow configuration of cache expiration times.
5. The system shall provide mechanisms to invalidate cache when necessary.

#### Language Model Integration

1. The system shall integrate with external language models via APIs.
2. The system shall implement rate limiting for language model API calls.
3. The system shall handle API failures gracefully with fallback mechanisms.
4. The system shall optimize prompts for accurate SQL generation.
5. The system shall track and log language model usage for cost management.

### User Interface Requirements

#### Chat Interface

1. The system shall provide a chat-style interface with user and system messages.
2. The system shall visually distinguish between user and system messages.
3. The system shall display a typing indicator during query processing.
4. The system shall support multi-line text input for complex questions.
5. The system shall provide a send button and keyboard shortcuts (Enter) to submit questions.

[DIAGRAM: Chat interface mockup showing user and system messages, typing indicator, and input area]

#### Session Management

1. The system shall display a list of user's previous chat sessions.
2. The system shall allow creation of new chat sessions.
3. The system shall allow renaming of chat sessions.
4. The system shall allow deletion of chat sessions.
5. The system shall group chat sessions by date (Today, Yesterday, This Week, etc.).

#### Result Presentation

1. The system shall display query results in an easily readable format.
2. The system shall provide collapsible SQL query display.
3. The system shall render appropriate visualizations for data.
4. The system shall display suggested follow-up questions as clickable chips.
5. The system shall provide a download button for query results.

[DIAGRAM: Result presentation mockup showing data visualization, SQL query, and follow-up suggestions]

#### Responsive Design

1. The system shall adapt to desktop, tablet, and mobile screen sizes.
2. The system shall support collapsible sidebar for small screens.
3. The system shall ensure all interactive elements are usable on touch devices.
4. The system shall maintain readability across different screen sizes.

#### Styling and Branding

1. The system shall support customizable color schemes.
2. The system shall support custom logos and branding elements.
3. The system shall use consistent typography throughout the interface.
4. The system shall implement visual hierarchy to focus attention on important elements.

### Future Enhancements

These features are not part of the initial MVP but should be planned for future releases:

#### Advanced Querying

1. Support for multi-part questions requiring multiple SQL queries
2. Query templates for common analysis patterns
3. Natural language database updates (INSERT, UPDATE, DELETE)
4. Custom SQL editing with verification

#### Collaboration

1. Shared team workspaces for queries
2. Query commenting and annotation
3. Export to presentation formats
4. Real-time collaborative querying

#### Advanced Visualization

1. Interactive dashboards from chat queries
2. Custom visualization settings
3. Saved/pinned visualizations
4. Advanced chart types (heatmaps, geographic maps)

#### Additional Integrations

1. Integration with business intelligence tools
2. Scheduled queries and alerts
3. Export to spreadsheet applications
4. Data dictionary and metadata integration

#### Advanced Intelligence

1. Proactive data insights and anomaly detection
2. Comparative analysis suggestions
3. Time series forecasting
4. Natural language query optimization recommendations

### Success Metrics

#### User Adoption

1. Number of active users (daily, weekly, monthly)
2. Query volume per user
3. Session duration and frequency
4. Feature utilization rates
5. User retention rate

#### Query Performance

1. Query translation accuracy rate
2. Average response time
3. Query success rate
4. Cache hit rate
5. Error recovery rate

#### Business Impact

1. Reduction in data team query requests
2. Time saved vs. traditional SQL queries
3. Increase in data-driven decisions
4. User satisfaction scores
5. Return on investment (ROI) based on time savings

#### Technical Performance

1. System uptime and availability
2. Resource utilization efficiency
3. Scalability under load
4. API response times
5. Cache effectiveness

## Glossary

| Term | Definition |
|------|------------|
| SQL | Structured Query Language, a programming language for managing relational databases |
| LLM | Large Language Model, an AI model trained on text data used for natural language processing |
| NL | Natural Language, human language as opposed to programming language |
| DDL | Data Definition Language, SQL statements used to define database schemas |
| BI | Business Intelligence, technology for data analysis and visualization |
| API | Application Programming Interface, a set of definitions for building and integrating software |
| Cache | Temporary storage of data to speed up future requests |
| Visualization | Graphical representation of data using charts and graphs |
| LRU | Least Recently Used, a cache eviction policy |
| KPI | Key Performance Indicator, a measurable value that demonstrates how effectively a company is achieving business objectives |
| Circuit Breaker | Design pattern used to detect failures and prevent cascade failures in distributed systems |