# Salesforce Health Check Dashboard

A web application that consolidates health metrics from various Salesforce systems, categorizes issues using Claude AI, and enables proactive resolution of potential problems.

## Product Requirements

### MVP Features
- Dashboard displaying health metrics from mock data sources
- AI-powered categorization of health issues using Claude 4 Sonnet
- Issue prioritization based on potential impact
- Actionable recommendations for issue resolution
- Basic filtering and search capabilities
- Mobile-responsive UI

### Phase 2 Features (Future)
- Integration with real data sources:
  - Salesforce Optimizer Health
  - Salesforce Security Health
  - Salesforce Limits Health
  - Salesforce Event Health from Splunk
  - Application Stability Health from Service Now
  - Salesforce Portal Health
  - Salesforce Exceptions Health
- JIRA ticket creation for issues
- Slack alerting based on priority
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
   - Integration with Claude AI via Heroku Inference

2. **Pydantic AI Integration**
   - Uses Heroku's Claude-4-Sonnet integration
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

## Technologies Used

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **AI**: Claude 4 Sonnet via Heroku Inference API
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, Plotly
- **Deployment**: Heroku

## Deployment

The application is deployed on Heroku with the following components:
- Web dyno running the FastAPI application
- Heroku PostgreSQL addon for database
- Heroku Inference addon for Claude AI integration

### Heroku Setup

```bash
# Create Heroku app
heroku create sf-health-agent

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini -a sf-health-agent

# Add Claude 4 Sonnet Inference addon
heroku addons:create heroku-inference:claude-4-sonnet -a sf-health-agent -- --region=us

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
   DATABASE_URL=postgresql://user:password@localhost:5432/sf_health
   HEROKU_INFERENCE_API_KEY=your-heroku-inference-api-key
   PORT=8000
   ```
4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Access the application at http://localhost:8000

## Important Links

- [Pydantic AI Documentation](https://ai.pydantic.dev/models/openai/#heroku-ai)
- [Heroku Inference API Documentation](https://devcenter.heroku.com/articles/heroku-inference-api-v1-chat-completions)
- [Pydantic AI Example Apps](https://ai.pydantic.dev/examples/slack-lead-qualifier/#conclusion)