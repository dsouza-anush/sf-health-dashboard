#!/bin/bash

# Script to test the Heroku Agents API directly with curl

# Get environment variables from Heroku
INFERENCE_KEY=$(heroku config:get INFERENCE_API_KEY -a sf-health-dashboard)
APP_NAME=$(heroku config:get APP_NAME -a sf-health-dashboard)

echo "Testing the Heroku Agents API with postgres_get_schema..."
curl -s https://us.inference.heroku.com/v1/agents/heroku \
-H "Authorization: Bearer $INFERENCE_KEY" \
-H "Content-Type: application/json" \
-d @- <<EOF
{
  "model": "claude-4-sonnet",
  "messages": [
    {
      "role": "user",
      "content": "Please analyze the schema of my database and tell me what tables are available."
    }
  ],
  "tools": [
    {
        "type": "heroku_tool",
        "name": "postgres_get_schema",
        "runtime_params": {
            "target_app_name": "$APP_NAME",
            "dyno_size": "standard-1x",
            "tool_params": {
                "db_attachment": "HEROKU_POSTGRESQL_COBALT"
            }
        }
    }
  ]
}
EOF

echo -e "\n\nTesting the Heroku Agents API with postgres_run_query..."
curl -s https://us.inference.heroku.com/v1/agents/heroku \
-H "Authorization: Bearer $INFERENCE_KEY" \
-H "Content-Type: application/json" \
-d @- <<EOF
{
  "model": "claude-4-sonnet",
  "messages": [
    {
      "role": "user",
      "content": "Please count how many health alerts are in the database and return the result."
    }
  ],
  "tools": [
    {
        "type": "heroku_tool",
        "name": "postgres_run_query",
        "runtime_params": {
            "target_app_name": "$APP_NAME",
            "dyno_size": "standard-1x",
            "tool_params": {
                "db_attachment": "HEROKU_POSTGRESQL_COBALT"
            }
        }
    }
  ]
}
EOF

echo -e "\n\nTesting the actual AI insights query with postgres_run_query..."
curl -s https://us.inference.heroku.com/v1/agents/heroku \
-H "Authorization: Bearer $INFERENCE_KEY" \
-H "Content-Type: application/json" \
-d @- <<EOF
{
  "model": "claude-4-sonnet",
  "messages": [
    {
      "role": "user",
      "content": "You are a Salesforce Health Analyzer specialized in analyzing health alert data.

Please analyze the health alerts from the last 7 days and provide 3 key insights:

1. Alert Pattern Detected: Identify any patterns or clusters in the alerts, such as increases/decreases in specific categories or notable frequency changes.
   
2. Potential Issue: Based on the alerts, identify a potential underlying issue that may need attention. Look for correlations or common root causes.
   
3. Suggested Action: Recommend a specific, actionable step that would help address the most critical issues identified.

Format your response as a JSON object with the following structure:
{
    \"alert_pattern\": {
        \"title\": \"Brief pattern title\",
        \"description\": \"Detailed description with numbers and percentages\"
    },
    \"potential_issue\": {
        \"title\": \"Brief issue title\",
        \"description\": \"Detailed description of the potential issue\"
    },
    \"suggested_action\": {
        \"title\": \"Brief action title\",
        \"description\": \"Detailed description of the recommended action\"
    },
    \"system_health_summary\": \"One sentence overall system health assessment\"
}"
    }
  ],
  "tools": [
    {
        "type": "heroku_tool",
        "name": "postgres_run_query",
        "runtime_params": {
            "target_app_name": "$APP_NAME",
            "dyno_size": "standard-1x",
            "tool_params": {
                "db_attachment": "HEROKU_POSTGRESQL_COBALT"
            }
        }
    }
  ]
}
EOF