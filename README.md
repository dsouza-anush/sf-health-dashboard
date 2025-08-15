# Salesforce Health Check Dashboard

A modern web application that consolidates health metrics from various Salesforce systems, categorizes issues using AI, and enables proactive resolution of potential problems with Slack notifications and JIRA ticket creation.

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/sf-health-dashboard)

## Product Requirements

### Features
- Dashboard displaying health metrics from various data sources
- AI-powered categorization of health issues
- Issue prioritization based on potential impact
- Actionable recommendations for issue resolution
- Basic filtering and search capabilities
- Mobile-responsive UI

### Implemented Features
- Dashboard displaying health metrics from mock data sources
- AI-powered categorization of health issues
- Issue prioritization based on potential impact
- Actionable recommendations for issue resolution
- Slack notification integration for high/critical priority alerts
- JIRA ticket creation for issues with full context
- Basic filtering and search capabilities
- Mobile-responsive UI

### Future Enhancements
- Integration with real data sources:
  - Salesforce Optimizer Health
  - Salesforce Security Health
  - Salesforce Limits Health
  - Salesforce Event Health from Splunk
  - Application Stability Health from Service Now
  - Salesforce Portal Health
  - Salesforce Exceptions Health
- Scheduled background health checks
- Historical trending analysis
- User authentication and role-based access

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                 Salesforce Health Check App             │
│                                                         │
├─────────────┬─────────────────────────┬─────────────────┤
│             │                         │                 │
│  Web UI     │   FastAPI Backend       │  Claude 4       │
│  (Browser)  │   (Python)              │  Sonnet AI      │
│             │                         │                 │
├─────────────┼─────────────────────────┼─────────────────┤
│             │                         │                 │
│  Bootstrap  │   Pydantic Models       │  Heroku         │
│  Jinja2     │   SQLAlchemy            │  Inference API  │
│  Plotly     │   Pydantic AI           │                 │
│             │                         │                 │
└─────────┬───┴──────────────┬──────────┴─────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────┐ ┌──────────────────┐
│                 │ │                  │
│  PostgreSQL     │ │  Future:         │
│  Database       │ │  External APIs   │
│                 │ │  (Phase 2)       │
│                 │ │                  │
└─────────────────┘ └──────────────────┘
```

### Key Components

1. **FastAPI Backend**
   - RESTful API endpoints for data access
   - Business logic for health metrics processing
   - Integration with Heroku Inference API

2. **AI Integration**
   - Uses Heroku Inference API for AI processing
   - Processes health alerts through structured schemas
   - Generates categorization, priority, and recommendations

3. **PostgreSQL Database**
   - Stores health metrics from various sources
   - Maintains AI analysis results and recommendations
   - Tracks issue resolution status

4. **Web UI**
   - Responsive dashboard built with Bootstrap
   - Interactive charts using Plotly
   - Server-side rendering with Jinja2 templates

5. **Slack Integration**
   - Automatic notifications for high and critical priority alerts
   - Rich message formatting with alert details
   - Links back to dashboard for further analysis

6. **JIRA Integration**
   - Creates tickets from alerts with full context
   - Includes AI analysis and recommendations
   - Maintains reference to tickets in the dashboard

## Technologies Used

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **AI**: Heroku Inference API
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, Plotly
- **Integrations**: Slack API, JIRA API
- **Deployment**: Heroku

## Deployment

The application is deployed on Heroku with the following components:
- Web dyno running the FastAPI application
- Heroku PostgreSQL addon for database
- Heroku Inference addon for Claude AI integration

### Heroku Setup

The easiest way to deploy is using the "Deploy to Heroku" button at the top of this README.

For manual deployment:

```bash
# Create Heroku app
heroku create sf-health-agent

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini -a sf-health-agent

# Add Claude AI Inference addon
heroku addons:create heroku-inference -a sf-health-agent -- --region=us

# Set additional environment variables
heroku config:set SLACK_API_KEY=your_slack_api_key -a sf-health-agent
heroku config:set SLACK_ALERTS_CHANNEL=#your-alerts-channel -a sf-health-agent
heroku config:set JIRA_API_TOKEN=your_jira_api_token -a sf-health-agent
heroku config:set JIRA_DOMAIN=https://your-company.atlassian.net -a sf-health-agent
heroku config:set JIRA_EMAIL=your-email@example.com -a sf-health-agent
heroku config:set JIRA_PROJECT_KEY=your_project_key -a sf-health-agent

# Deploy application
git push heroku main

# Seed the database with initial data
heroku run python -c "from database.seed import seed_database; seed_database()"
```

## Local Development

1. Clone the repository
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file:
   ```
   # Required variables
   DATABASE_URL=postgresql://user:password@localhost:5432/sf_health
   HEROKU_INFERENCE_API_KEY=your-heroku-inference-api-key
   PORT=8000
   
   # Optional Slack integration
   SLACK_API_KEY=your-slack-api-key
   SLACK_ALERTS_CHANNEL=#your-alerts-channel
   APP_HOST=localhost:8000
   
   # Optional JIRA integration
   JIRA_API_TOKEN=your-jira-api-token
   JIRA_DOMAIN=https://your-company.atlassian.net
   JIRA_EMAIL=your-email@example.com
   JIRA_PROJECT_KEY=your-project-key
   ```
4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Access the application at http://localhost:8000

## Important Links

- [Heroku Inference API Documentation](https://devcenter.heroku.com/articles/heroku-inference-api-v1-chat-completions)
- [Slack API Documentation](https://api.slack.com/messaging/webhooks)
- [JIRA API Documentation](https://developer.atlassian.com/server/jira/platform/rest-apis/)

## Milestones

1. 🏆 Initial Setup and Database Models
2. 🏆 AI Categorization with Claude
3. 🏆 Slack Integration for High/Critical Alerts
4. 🏆 JIRA Integration for Ticket Creation
5. 🏆 Deployment and Documentation