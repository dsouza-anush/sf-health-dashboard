# Database Setup for Heroku Agents API Integration

This document outlines the process for setting up and configuring the Heroku Postgres database to work properly with the Heroku Agents API and AI Insights feature.

## Prerequisites

- Heroku CLI installed and authenticated
- Admin access to the Heroku app (`sf-health-dashboard`)
- Standard-0 or higher database plan

## Database Requirements for Heroku Agents API

The Heroku Agents API's `postgres_run_query` tool requires:

1. A Standard-0 or higher database plan
2. A follower database configuration (read-only replica)
3. Standard-1x or higher dyno type for the agent execution

## Setup Steps

### 1. Upgrade to Standard-0 Database Plan

```bash
# Create a new Standard-0 database
heroku addons:create heroku-postgresql:standard-0 --app sf-health-dashboard

# Wait for the database to be fully provisioned
heroku pg:wait -a sf-health-dashboard HEROKU_POSTGRESQL_NEW_COLOR_URL

# Promote the new database to be the primary database
heroku pg:promote HEROKU_POSTGRESQL_NEW_COLOR_URL -a sf-health-dashboard
```

### 2. Wait for Fork/Follow Functionality

Newly created databases may not immediately support Fork/Follow functionality. You'll need to wait for some time (typically a few hours) before this feature becomes available.

Use the provided script to check database status:

```bash
# Check current status
python3 scripts/check_db_status.py sf-health-dashboard

# Monitor status continuously (checks every 5 minutes)
python3 scripts/check_db_status.py sf-health-dashboard --monitor --interval 300
```

### 3. Create Follower Database

Once Fork/Follow functionality is available, create a follower database:

```bash
heroku addons:create heroku-postgresql:standard-0 --app sf-health-dashboard -- --follow DATABASE_URL
```

This will create a read-only replica of your primary database that can be safely queried by the Heroku Agents API.

### 4. Update Environment Configuration

After creating the follower database, set an environment variable to explicitly specify the follower database URL:

```bash
# Get the database URL of the follower and set it as DATABASE_FOLLOWER_URL
heroku config:set DATABASE_FOLLOWER_URL=`heroku config:get HEROKU_POSTGRESQL_NEW_FOLLOWER_COLOR_URL -a sf-health-dashboard` -a sf-health-dashboard
```

## Troubleshooting

### Common Issues

1. **"Target database is not a replica" Error**
   - Cause: The database being used is not a follower database
   - Solution: Create a proper follower database as described above

2. **"The database you are attempting to follow is still too new" Error**
   - Cause: The primary database was recently created and does not yet support Fork/Follow
   - Solution: Wait for some time (typically a few hours) and try again

3. **"You can't use Basic. You can only use Standard-1X..." Error**
   - Cause: The dyno type specified for the agent is not sufficient
   - Solution: Set the dyno_size to "standard-1x" in the API request

### Checking Database Status

```bash
# Check database configuration and status
heroku pg:info -a sf-health-dashboard
```

## Fallback Mechanism

The `heroku_insights_service.py` service includes a fallback mechanism that will provide mock insights when the Heroku Agents API is not available or encounters errors. This ensures that the AI insights feature remains functional during the database configuration process.

When the proper follower database setup is complete, the service will automatically switch to using real-time AI-generated insights based on the actual database data.