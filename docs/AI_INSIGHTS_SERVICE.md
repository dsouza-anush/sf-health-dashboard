# AI Insights Service Documentation

## Overview

The AI Insights Service is a core component of the Salesforce Health Dashboard that provides intelligent analysis of health alert data. It uses Claude AI through the Heroku Agents API to analyze alert patterns, identify potential issues, and suggest actions based on the data in the PostgreSQL database.

## Architecture

The service follows this architecture:

1. **Frontend Request**: User requests AI insights from the dashboard UI
2. **FastAPI Endpoint**: Handles the request via `/api/insights/` endpoint
3. **HerokuInsightsService**: Connects to the Heroku Agents API
4. **Follower Database**: Uses the COBALT follower database for read-only queries
5. **SSE Response**: Processes streaming events from the Heroku Agents API
6. **JSON Response**: Returns structured insights to the frontend

## Database Configuration

The service requires a specific database configuration:

- **Primary Database**: Used for all normal application functions (AMBER)
- **Follower Database**: Required by Heroku Agents API for analytics (COBALT)
  
### Why Follower Databases are Required

The Heroku Agents API **strictly requires** a follower database for several critical reasons:

1. **Security**: Follower databases are read-only, preventing any accidental writes from LLM-generated SQL
2. **Performance**: Separates analytical queries from transactional workloads
3. **Data Consistency**: Ensures the AI is working with a consistent view of the data
4. **Resource Isolation**: Prevents LLM-generated queries from impacting application performance

Without a properly configured follower database, the Heroku Agents API will explicitly reject queries with the error `"Target database is not a replica"`. If the follower database is missing or improperly configured, the service will fall back to a default message.

### Current Configuration

- Primary DB: `HEROKU_POSTGRESQL_AMBER` (standard-0)
- Follower DB: `HEROKU_POSTGRESQL_COBALT` (standard-0, follows AMBER)

### Creating a Follower Database

If the follower database needs to be recreated, use this command:

```bash
heroku addons:create heroku-postgresql:standard-0 --app sf-health-dashboard -- --follow DATABASE_URL
```

After creation, you need to set it as the COBALT database:

```bash
heroku pg:promote HEROKU_POSTGRESQL_COLOR_URL --as HEROKU_POSTGRESQL_COBALT -a sf-health-dashboard
```

Replace `COLOR_URL` with the actual color assigned by Heroku (like PURPLE, CYAN, etc.)

## API Usage

### Endpoint

```
GET /api/insights/?time_range={time_range}
```

Where `time_range` is one of:
- `day` (last 24 hours)
- `week` (last 7 days, default)
- `month` (last 30 days)

### Response Format

```json
{
  "alert_pattern": {
    "title": "Brief pattern title",
    "description": "Detailed description with numbers and percentages"
  },
  "potential_issue": {
    "title": "Brief issue title",
    "description": "Detailed description of the potential issue"
  },
  "suggested_action": {
    "title": "Brief action title",
    "description": "Detailed description of the recommended action"
  },
  "system_health_summary": "One sentence overall system health assessment",
  "generated_at": "2025-08-15T17:44:12.003262",
  "time_range": "week",
  "is_fallback": false
}
```

When the AI service encounters an error, it returns a fallback response with `"is_fallback": true`.

## Implementation Details

### Heroku Agents API

The service uses the Heroku Agents API with Claude to analyze the database. This API allows Claude to execute SQL queries against the database to generate insights.

#### Configuration

- **Model**: claude-4-sonnet
- **Tool**: postgres_run_query (allows Claude to query the database)
- **Response Format**: Server-Sent Events (SSE)
- **Timeout**: 120 seconds
- **Dyno Size**: standard-1x (for query execution)

#### Key Limitations

1. **Maximum Tool Calls**: The API limits Claude to 3 tool calls per request. If Claude tries to run more than 3 queries, the request will fail with `"tool exceeded maximum calls (3)"`. This means Claude must get all necessary insights within those 3 queries.

2. **Follower Database Only**: The API will only execute queries against follower databases. Attempts to use primary databases will fail.

3. **Timeout Constraints**: Complex queries might exceed the timeout, especially with large datasets.

#### How it Works

When the user requests insights:

1. The app sends a request to the Heroku Agents API with the prompt and tool configuration
2. Claude analyzes the prompt and decides which queries to run
3. Claude executes SQL queries (up to 3) against the follower database
4. Claude analyzes the data returned from these queries
5. Claude generates insights based on the data and returns them as JSON
6. The app processes this response and displays it to the user

The Heroku Agents API handles running the queries in a secure sandbox environment.

### SSE Response Handling

The Heroku Agents API returns responses as Server-Sent Events (SSE), which requires special handling:

1. Set `Accept: text/event-stream` header in the request
2. Parse the streaming response line by line
3. Process events based on the event type (`event:` field)
4. Extract the final message from the completion event

Example SSE format:
```
event: message
data: {"object": "chat.completion", "choices": [{"message": {"content": "..."}}]}

event: done
data: [DONE]
```

### Error Handling

The service implements robust error handling:

1. **Database Configuration Errors**: If the follower database is not properly configured
2. **API Timeouts**: If the Heroku Agents API takes too long to respond
3. **Tool Call Limits**: If Claude exceeds the maximum number of tool calls (3)
4. **Response Parsing Errors**: If the SSE response cannot be properly parsed

In all error cases, the service falls back to a default response with appropriate error messages.

## Testing

### Direct API Testing

Test the endpoint directly:

```bash
curl https://sf-health-dashboard-c0d39041d119.herokuapp.com/api/insights/
```

### Testing with the Heroku Agents API

Use the test script to directly test the Heroku Agents API:

```bash
./scripts/test_heroku_agents_api.sh
```

This script tests:
1. postgres_get_schema - Retrieves database structure
2. postgres_run_query - Counts alerts
3. postgres_run_query - Runs the full insights query

### Common Errors and Solutions

1. **"Missing follower database"**
   - Solution: Create a follower database with:
   ```
   heroku addons:create heroku-postgresql:standard-0 --app sf-health-dashboard -- --follow DATABASE_URL
   ```

2. **"Tool exceeded maximum calls (3)"**
   - This occurs when Claude tries to run more than 3 database queries
   - Solution: Optimize the prompt to get all needed information in 3 or fewer queries

3. **"Indentation Error"**
   - Python is sensitive to indentation
   - Solution: Carefully check the code for consistent indentation, especially in try/except blocks

4. **"Target database is not a replica"**
   - Solution: Ensure the `db_attachment` parameter is set to the follower database attachment name

## Debugging

For debugging issues with the AI insights service:

1. **Check Heroku Logs**:
   ```bash
   heroku logs -n 100 -a sf-health-dashboard
   ```

2. **Check Database Configuration**:
   ```bash
   heroku pg:info -a sf-health-dashboard
   ```

3. **Verify Follower Status**:
   ```bash
   heroku pg:info HEROKU_POSTGRESQL_COBALT -a sf-health-dashboard
   ```

4. **Test the Heroku Agents API directly**:
   ```bash
   ./scripts/test_heroku_agents_api.sh
   ```

## Best Practices for Future Development

1. **Maintain Proper DB Configuration**: Always ensure the follower database is properly configured
2. **Optimize API Prompts**: Keep queries efficient to avoid exceeding the 3-query limit
3. **Handle SSE Properly**: Always use proper SSE parsing for streaming responses
4. **Add Comprehensive Logging**: Log key events and errors for easier debugging
5. **Set Appropriate Timeouts**: API calls should have reasonable timeouts (30+ seconds)
6. **Add Fallback Mechanisms**: Always provide fallback responses for when AI is unavailable

## Environment Variables

The service requires these environment variables:

- `HEROKU_INFERENCE_API_KEY` or `INFERENCE_API_KEY`: API key for Claude
- `INFERENCE_MODEL_ID` (optional, defaults to claude-4-sonnet)
- `APP_NAME` or `HEROKU_APP_NAME`: The Heroku app name

## Key Files

- `/services/heroku_insights_service.py`: Main service implementation
- `/app/api.py`: API endpoint definition
- `/scripts/test_heroku_agents_api.sh`: Test script for the API