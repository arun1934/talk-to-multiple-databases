# API Documentation - SQL DB Chat System

This documentation covers the API endpoints provided by the SQL DB Chat System, which enables natural language querying of databases.

## Base URL

All endpoints are relative to the base URL of your deployment:

```
https://your-domain.com/
```

## Authentication

Authentication is not covered in this documentation. Implement appropriate authentication methods based on your security requirements.

## Endpoints

### Query Endpoint

Submit a natural language question to be translated to SQL and executed.

**URL**: `/query`

**Method**: `POST`

**Request Body**:

| Field | Type | Description |
|-------|------|-------------|
| question | string | The natural language question to be processed |
| session_id | string | (Optional) Unique identifier for conversation tracking |

**Example Request**:

```json
{
  "question": "How many users registered last month?",
  "session_id": "user-123"
}
```

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| task_id | string | The ID of the asynchronous task processing the query |

**Example Response**:

```json
{
  "task_id": "8f1b3c2e-4a5d-6e7f-8g9h-0i1j2k3l4m5n"
}
```

**Status Codes**:

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful - task created |
| 400 | Bad request - invalid parameters |
| 500 | Server error |

---

### Task Result Endpoint

Retrieve the results of a previously submitted query.

**URL**: `/result/{task_id}`

**Method**: `GET`

**URL Parameters**:

| Parameter | Description |
|-----------|-------------|
| task_id | The ID of the task returned from the query endpoint |

**Example Request**:

```
GET /result/8f1b3c2e-4a5d-6e7f-8g9h-0i1j2k3l4m5n
```

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| status | string | Status of the task: "processing", "completed", or "failed" |
| result | object | (If completed) The query results |
| error | string | (If failed) Error message |

**Result Object**:

| Field | Type | Description |
|-------|------|-------------|
| sql | string | The generated SQL query |
| formatted_result | string | Natural language summary of results |
| suggestions | array | List of suggested follow-up questions |
| table_result | object | Structured data for table display |

**Table Result Object**:

| Field | Type | Description |
|-------|------|-------------|
| columns | array | List of column names |
| rows | array | List of row data |

**Example Response (Processing)**:

```json
{
  "status": "processing"
}
```

**Example Response (Completed)**:

```json
{
  "status": "completed",
  "result": {
    "sql": "SELECT COUNT(*) FROM users WHERE created_at >= DATE_TRUNC('month', NOW() - INTERVAL '1 month') AND created_at < DATE_TRUNC('month', NOW())",
    "formatted_result": "There were 254 users who registered last month.",
    "suggestions": [
      "How does this compare to the previous month?",
      "What was the registration trend over the past six months?",
      "How many of these users have completed their profile?"
    ],
    "table_result": {
      "columns": ["count"],
      "rows": [[254]]
    }
  }
}
```

**Example Response (Failed)**:

```json
{
  "status": "failed",
  "error": "Failed to execute SQL query: relation 'user' does not exist"
}
```

**Status Codes**:

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 404 | Task not found |
| 500 | Server error |

---

### Visualization Recommendation Endpoint

Get visualization recommendations for query results.

**URL**: `/visualization-recommendation`

**Method**: `POST`

**Request Body**:

| Field | Type | Description |
|-------|------|-------------|
| question | string | The original natural language question |
| sqlQuery | string | The SQL query that was executed |
| results | string | JSON string of the query results |

**Example Request**:

```json
{
  "question": "What are the monthly sales figures for the past year?",
  "sqlQuery": "SELECT date_trunc('month', sale_date) as month, SUM(amount) as total FROM sales GROUP BY month ORDER BY month",
  "results": "[{\"month\":\"2024-01-01\",\"total\":12500},{\"month\":\"2024-02-01\",\"total\":15200}]"
}
```

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| visualization | string | Recommended visualization type (bar, line, pie, scatter, none) |
| visualization_reason | string | Explanation for the recommendation |

**Example Response**:

```json
{
  "visualization": "line",
  "visualization_reason": "A line graph is recommended because the data shows a time-based trend with monthly sales figures across multiple periods."
}
```

**Status Codes**:

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 400 | Bad request - invalid parameters |
| 500 | Server error |

## Error Responses

All endpoints may return error responses with the following structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Response Formats

### SQL Query Format

The SQL queries generated by the system are compatible with PostgreSQL. Example query:

```sql
SELECT 
  date_trunc('month', created_at) AS month,
  COUNT(*) AS user_count
FROM 
  users
WHERE 
  created_at >= DATE_TRUNC('year', NOW())
GROUP BY 
  month
ORDER BY 
  month;
```

### Table Result Format

The table_result object provides structured data suitable for rendering in a table or chart:

```json
{
  "columns": ["month", "user_count"],
  "rows": [
    ["2024-01-01", 120],
    ["2024-02-01", 145],
    ["2024-03-01", 189],
    ["2024-04-01", 254]
  ]
}
```

### Visualization Types

The visualization recommendation endpoint returns one of the following visualization types:

- `bar`: Bar chart for comparing categorical data
- `horizontal_bar`: Horizontal bar chart for comparing categories with long names
- `line`: Line chart for time series or trend data
- `pie`: Pie chart for showing proportions of a whole
- `scatter`: Scatter plot for showing relationships between variables
- `none`: No visualization recommended

## Pagination

The API currently does not implement pagination for query results. For large result sets, consider implementing frontend pagination.

## Rate Limiting

The API may implement rate limiting to prevent abuse. If rate limiting is in effect, the API will return a 429 status code with a Retry-After header.

## Example Usage

### Complete Request Flow

1. Submit a question:

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "How many users registered each month this year?",
       "session_id": "user-123"
     }'
```

Response:
```json
{
  "task_id": "8f1b3c2e-4a5d-6e7f-8g9h-0i1j2k3l4m5n"
}
```

2. Check task status and get results:

```bash
curl "http://localhost:8000/result/8f1b3c2e-4a5d-6e7f-8g9h-0i1j2k3l4m5n"
```

Response:
```json
{
  "status": "completed",
  "result": {
    "sql": "SELECT date_trunc('month', created_at) AS month, COUNT(*) AS user_count FROM users WHERE created_at >= DATE_TRUNC('year', NOW()) GROUP BY month ORDER BY month",
    "formatted_result": "In 2024, user registrations by month were: January: 120 users, February: 145 users, March: 189 users, and April: 254 users. This shows a consistent growth in user registrations each month.",
    "suggestions": [
      "What was the percentage growth in user registrations month over month?",
      "How do these registration numbers compare to the same months last year?",
      "Which registration source brought in the most users?"
    ],
    "table_result": {
      "columns": ["month", "user_count"],
      "rows": [
        ["2024-01-01", 120],
        ["2024-02-01", 145],
        ["2024-03-01", 189],
        ["2024-04-01", 254]
      ]
    }
  }
}
```

3. Get visualization recommendation:

```bash
curl -X POST "http://localhost:8000/visualization-recommendation" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "How many users registered each month this year?",
       "sqlQuery": "SELECT date_trunc('\''month'\'', created_at) AS month, COUNT(*) AS user_count FROM users WHERE created_at >= DATE_TRUNC('\''year'\'', NOW()) GROUP BY month ORDER BY month",
       "results": "[{\"month\":\"2024-01-01\",\"user_count\":120},{\"month\":\"2024-02-01\",\"user_count\":145},{\"month\":\"2024-03-01\",\"user_count\":189},{\"month\":\"2024-04-01\",\"user_count\":254}]"
     }'
```

Response:
```json
{
  "visualization": "line",
  "visualization_reason": "A line graph is recommended because the data shows a trend over time with monthly intervals, making it easy to visualize the progression of user registrations throughout the year."
}
```

## Webhooks

The current API does not implement webhooks. For long-running queries, implement a polling strategy using the task result endpoint.

## API Changes

The API is subject to change in future versions. Major changes will be communicated through updated documentation.
