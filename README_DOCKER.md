# Docker Setup Guide - SQL DB Chat System

This guide provides detailed instructions for setting up and running the SQL DB Chat System using Docker.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/) (version 20.10.0 or later)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0.0 or later)
- Git (for cloning the repository)

## Docker Configuration

The system uses a multi-container setup managed by Docker Compose:

- **app**: FastAPI application
- **celery_worker**: Celery worker for async processing
- **redis**: Redis for caching and message broker

## Quick Start

### 1. Clone the Repository

```
```

### 2. Configure Environment Variables

Create a `.env` file in the app directory:

```bash
# Database connection URL
DATABASE_URL=postgresql+asyncpg://postgres:password@host.docker.internal:5432/yourdb

# Redis URL for caching
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# OpenAI API key - using your LiteLLM key
OPENAI_API_KEY=your_api_key

# LiteLLM settings
LITELLM_API_BASE=https://lmlitellm.landmarkgroup.com
LITELLM_AUTH_HEADER=Bearer your_auth_token
LITELLM_MODEL=gpt-41-mini

# LLM cache settings
ENABLE_LLM_CACHE=true
LLM_CACHE_TTL=300

# LLM temperature settings
GENERATION_TEMPERATURE=0.0
SUMMARY_TEMPERATURE=0.3
SUGGESTION_TEMPERATURE=0.5
```

> **Important**: Replace placeholders with your actual credentials. Never commit the `.env` file to version control.

### 3. Build and Start the Containers

```bash
docker-compose build
docker-compose up -d
```

This will:
- Build the Docker images
- Create and start the containers in detached mode
- Set up the network between containers

### 4. Verify Installation

Check if the containers are running:

```bash
docker-compose ps
```

You should see all containers with the `Up` status.

Access the API at `http://localhost:8000/docs` to see the Swagger UI.

## Container Details

### FastAPI App Container

- **Image**: Custom Python 3.9 image
- **Ports**: 8000 (exposed to host)
- **Volumes**: None (application code is bundled in the image)
- **Dependencies**: Redis, Database

### Celery Worker Container

- **Image**: Same as the app container
- **Ports**: None (no exposed ports)
- **Volumes**: None
- **Dependencies**: Redis, Database

### Redis Container

- **Image**: redis:alpine
- **Ports**: 6379 (exposed to host)
- **Volumes**: None (data not persisted between restarts)

## Docker Compose File


## Common Operations

### View Logs

```bash
# View logs for all containers
docker-compose logs

# View logs for a specific container
docker-compose logs app
docker-compose logs celery_worker
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f
```

### Restart Containers

```bash
# Restart all containers
docker-compose restart

# Restart a specific container
docker-compose restart app
```

### Stop Containers

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (clears Redis data)
docker-compose down -v
```

### Rebuild After Code Changes

```bash
# Rebuild and restart containers
docker-compose up -d --build
```

## Database Connection

The application connects to your PostgreSQL database using the `DATABASE_URL` environment variable. There are several options:

### 1. Using a Database on the Host Machine

If PostgreSQL is running on your host machine, use:

```
DATABASE_URL=postgresql+asyncpg://postgres:password@host.docker.internal:5432/yourdb
```

`host.docker.internal` is a special DNS name that resolves to the host IP address.

### 2. Using an External Database

For a cloud database or database on another server:

```
DATABASE_URL=postgresql+asyncpg://username:password@your-db-host.com:5432/yourdb
```

## Troubleshooting

### Container Fails to Start

Check the logs:

```bash
docker-compose logs app
```

Common issues:
- Database connection error
- Redis connection error
- Missing environment variables

### Redis Connection Issues

Ensure Redis is running:

```bash
docker-compose ps redis
```

Check Redis logs:

```bash
docker-compose logs redis
```


## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| DATABASE_URL | PostgreSQL connection string | Yes | - |
| REDIS_URL | Redis connection URL | Yes | - |
| REDIS_HOST | Redis hostname | Yes | - |
| REDIS_PORT | Redis port | Yes | - |
| OPENAI_API_KEY | API key for LiteLLM | Yes | - |
| LITELLM_API_BASE | LiteLLM API base URL | Yes | - |
| LITELLM_AUTH_HEADER | Authentication header for LiteLLM | Yes | - |
| LITELLM_MODEL | Model name to use | Yes | - |
| ENABLE_LLM_CACHE | Toggle LLM caching | No | true |
| LLM_CACHE_TTL | Cache time-to-live (seconds) | No | 300 |
| GENERATION_TEMPERATURE | Temperature for SQL generation | No | 0.0 |
| SUMMARY_TEMPERATURE | Temperature for summaries | No | 0.3 |
| SUGGESTION_TEMPERATURE | Temperature for follow-up suggestions | No | 0.5 |
