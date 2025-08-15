# Salesforce Health Dashboard - System Architecture

## Overview Diagram

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                                                                                │
│                      Salesforce Health Dashboard System                        │
│                                                                                │
├────────────────┬────────────────────────┬──────────────────┬──────────────────┤
│                │                        │                  │                  │
│                │                        │                  │                  │
│  ┌────────┐    │       ┌──────────┐     │   ┌─────────┐    │   ┌─────────┐    │
│  │        │    │       │          │     │   │         │    │   │         │    │
│  │Web UI  │◄───┼───────┤ FastAPI  │◄────┼───┤PostgreSQL│    │   │ Claude  │    │
│  │Browser │    │       │Endpoints │     │   │Database  │    │   │   AI    │    │
│  │        │    │       │          │     │   │         │    │   │         │    │
│  └────┬───┘    │       └─────┬────┘     │   └────┬────┘    │   └────┬────┘    │
│       │        │             │          │        │         │        │         │
│       ▼        │             ▼          │        ▼         │        ▼         │
│  ┌────────┐    │       ┌──────────┐     │   ┌─────────┐    │   ┌─────────┐    │
│  │        │    │       │          │     │   │  Data   │    │   │ Heroku  │    │
│  │   UI   │◄───┼───────┤ Service  │◄────┼───┤  Models │    │   │Inference│    │
│  │Templates│   │       │  Layer   │     │   │         │    │   │   API   │    │
│  │        │    │       │          │     │   │         │    │   │         │    │
│  └────────┘    │       └──────┬───┘     │   └─────────┘    │   └─────────┘    │
│                │              │         │                  │                  │
└────────────────┴──────────────┼─────────┴──────────────────┴──────────────────┘
                                │
                                ▼
                ┌───────────────┬───────────────┐
                │               │               │
          ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
          │           │   │           │   │           │
          │   Slack   │   │   JIRA    │   │   Email   │
          │ Alerting  │   │  Tickets  │   │ Reporting │
          │           │   │           │   │           │
          └───────────┘   └───────────┘   └───────────┘
```

## Detailed Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                                  │
│                                                                         │
│  ┌─────────────┐    ┌───────────────┐    ┌─────────────────────────┐    │
│  │             │    │               │    │                         │    │
│  │  Dashboard  │    │  Alert Detail │    │  Alert Management UI    │    │
│  │     UI      │    │     View      │    │                         │    │
│  │             │    │               │    │                         │    │
│  └──────┬──────┘    └───────┬───────┘    └────────────┬────────────┘    │
│         │                   │                         │                 │
└─────────┼───────────────────┼─────────────────────────┼─────────────────┘
          │                   │                         │
          ▼                   ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Layer                                     │
│                                                                         │
│  ┌─────────────┐    ┌───────────────┐    ┌─────────────────────────┐    │
│  │             │    │               │    │                         │    │
│  │  GET /api/  │    │GET /api/alerts│    │ POST /api/alerts/{id}/  │    │
│  │  insights/  │    │     /{id}     │    │      categorize         │    │
│  │             │    │               │    │                         │    │
│  └──────┬──────┘    └───────┬───────┘    └────────────┬────────────┘    │
│         │                   │                         │                 │
└─────────┼───────────────────┼─────────────────────────┼─────────────────┘
          │                   │                         │
          ▼                   ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Service Layer                                   │
│                                                                         │
│  ┌─────────────┐    ┌───────────────┐    ┌─────────────────────────┐    │
│  │   Heroku    │    │               │    │                         │    │
│  │  Insights   │    │ Health Service│    │      AI Service         │    │
│  │  Service    │    │               │    │                         │    │
│  │             │    │               │    │                         │    │
│  └──────┬──────┘    └───────┬───────┘    └────────────┬────────────┘    │
│         │                   │                         │                 │
│         │            ┌──────┴──────┐                  │                 │
│         │            │             │                  │                 │
│         │            │ Slack/JIRA  │                  │                 │
│         │            │  Service    │                  │                 │
│         │            │             │                  │                 │
│         │            └─────────────┘                  │                 │
│         │                                             │                 │
└─────────┼─────────────────────────────────────────────┼─────────────────┘
          │                                             │
          ▼                                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        External Services                                │
│                                                                         │
│  ┌───────────────────────┐              ┌───────────────────────────┐   │
│  │                       │              │                           │   │
│  │   Heroku Agents API   │              │      Heroku Inference     │   │
│  │   (Claude AI + DB)    │              │         (Claude AI)       │   │
│  │                       │              │                           │   │
│  └───────────┬───────────┘              └───────────────┬───────────┘   │
│              │                                          │               │
│              ▼                                          ▼               │
│  ┌───────────────────────┐              ┌───────────────────────────┐   │
│  │                       │              │                           │   │
│  │   Primary Database    │              │    Follower Database      │   │
│  │     (AMBER/RW)        │              │     (COBALT/RO)           │   │
│  │                       │              │                           │   │
│  └───────────────────────┘              └───────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow for AI Insights

```
┌──────────┐      ┌───────────┐      ┌────────────────┐      ┌─────────────┐
│          │  1   │           │  2   │                │  3   │             │
│  User    ├─────►│  FastAPI  ├─────►│    Heroku      ├─────►│ Heroku      │
│ Browser  │      │  Endpoint │      │ Insights Svc   │      │ Agents API  │
│          │◄─────┤           │◄─────┤                │◄─────┤             │
└──────────┘  8   └───────────┘  7   └────────────────┘  6   └─────┬───────┘
                                                               4    │
                                                                    ▼
                                                             ┌─────────────┐
                                                             │             │
                                                             │  Follower   │
                                                             │  Database   │
                                                             │  (COBALT)   │
                                                             │             │
                                                             └─────┬───────┘
                                                               5   │
                                                                   ▼
                                                             ┌─────────────┐
                                                             │             │
                                                             │   Claude    │
                                                             │     AI      │
                                                             │             │
                                                             └─────────────┘
```

### Data Flow Steps:

1. User requests AI insights from dashboard UI
2. FastAPI endpoint receives request and calls Heroku Insights Service
3. Heroku Insights Service sends request to Heroku Agents API
4. Heroku Agents API connects to the follower database (COBALT)
5. Claude AI receives database data and generates insights
6. AI-generated insights returned as SSE stream
7. Insights parsed and processed by service layer
8. Formatted insights displayed to user in dashboard

## Alert Categorization Flow

```
┌──────────┐      ┌───────────┐      ┌────────────────┐      ┌─────────────┐
│          │  1   │           │  2   │                │  3   │             │
│  User    ├─────►│  FastAPI  ├─────►│    AI          ├─────►│ Heroku      │
│ Browser  │      │  Endpoint │      │  Service       │      │Inference API│
│          │◄─────┤           │◄─────┤                │◄─────┤             │
└──────────┘  6   └───────────┘  5   └────────────────┘  4   └─────────────┘
```

### Alert Categorization Steps:

1. User clicks "Categorize" on an alert
2. FastAPI endpoint receives request and calls AI Service
3. AI Service sends structured request to Heroku Inference API
4. Claude AI analyzes alert data and returns categorization
5. AI results stored in database and returned to endpoint
6. UI updated with new alert categorization

## Notification Flow

```
┌──────────┐      ┌───────────┐      ┌────────────────┐      ┌─────────────┐
│          │      │           │      │                │  1   │             │
│  Health  ├─────►│  Database ├─────►│    Slack       ├─────►│   Slack     │
│  Alert   │      │           │      │   Service      │      │  Workspace  │
│          │      │           │      │                │      │             │
└──────────┘      └───────────┘      └────┬───────────┘      └─────────────┘
                                          │
                                          │ 2
                                          ▼
                                     ┌────────────┐
                                     │            │
                                     │   JIRA     │
                                     │  Service   │
                                     │            │
                                     └─────┬──────┘
                                           │
                                           │ 3
                                           ▼
                                     ┌────────────┐
                                     │            │
                                     │   JIRA     │
                                     │  Project   │
                                     │            │
                                     └────────────┘
```

### Notification Steps:

1. High/Critical alerts trigger Slack notifications
2. User can create JIRA tickets from alerts
3. JIRA tickets include all context and AI analysis

## Database Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                    PostgreSQL Database                              │
│                                                                     │
│  ┌───────────────────────┐            ┌────────────────────────┐    │
│  │                       │            │                        │    │
│  │   Primary Database    │◄───────────┤   Follower Database    │    │
│  │  (Read-Write Access)  │ Replication│   (Read-Only Access)   │    │
│  │                       │            │                        │    │
│  └───────┬───────────────┘            └────────────┬───────────┘    │
│          │                                         │                │
│          ▼                                         ▼                │
│  ┌───────────────────────┐            ┌────────────────────────┐    │
│  │                       │            │                        │    │
│  │  Application Access   │            │   AI Query Access      │    │
│  │   (All Operations)    │            │ (Analytics/Insights)   │    │
│  │                       │            │                        │    │
│  └───────────────────────┘            └────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Tables

```
┌──────────────────────┐       ┌───────────────────────┐
│                      │       │                       │
│    health_alerts     │       │    ai_categories      │
│                      │       │                       │
├──────────────────────┤       ├───────────────────────┤
│ id (PK)              │       │ id (PK)               │
│ title                │       │ name                  │
│ description          │       │ description           │
│ category             │◄──────┤ priority              │
│ source_system        │       │                       │
│ raw_data             │       └───────────────────────┘
│ created_at           │                  ▲
│ updated_at           │                  │
│ ai_category          │──────────────────┘
│ ai_priority          │
│ ai_summary           │
│ ai_recommendation    │
│ is_resolved          │
│ jira_ticket_id       │
│ slack_alert_sent     │
└──────────────────────┘
```