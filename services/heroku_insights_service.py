import os
import json
import logging
import traceback
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Set up logger
logger = logging.getLogger(__name__)

# Cache for storing insights to avoid repeated API calls
insights_cache = {}
CACHE_TTL_SECONDS = 900  # 15 minutes

class HerokuInsightsService:
    def __init__(self):
        # Get API key from environment - check all possible variable names
        self.api_key = os.getenv("HEROKU_INFERENCE_API_KEY") or os.getenv("INFERENCE_API_KEY") or os.getenv("INFERENCE_KEY")
        
        # Get model ID and URL from environment
        self.model_id = os.getenv("INFERENCE_MODEL_ID", "claude-4-sonnet")
        self.inference_url = os.getenv("INFERENCE_URL", "https://us.inference.heroku.com")
        self.agents_endpoint = f"{self.inference_url}/v1/agents/heroku"
        
        # Get app name from environment
        self.app_name = os.getenv("APP_NAME") or os.getenv("HEROKU_APP_NAME")
        
        # Use COBALT database which is a follower database (required by Heroku Agents API)
        # Do not use the URL directly - instead use the attachment name which Heroku Agents API expects
        self.db_attachment = "HEROKU_POSTGRESQL_COBALT" 
        self.is_follower_db = True  # COBALT is a follower database
        
        # Check for required configuration
        if not self.api_key:
            logger.warning("No inference API key found. AI insights will not work.")
        if not self.app_name:
            logger.warning("No Heroku app name found. AI insights will not work.")
        if not self.db_url:
            logger.warning("No database URL found. AI insights will not work.")
            
        # Check database configuration
        self.using_standard_db = True  # We assume Standard DB for Heroku
        self.fork_follow_available = True  # COBALT is a follower database
        
        # Log database information
        logger.info(f"Using follower database '{self.db_attachment}' for AI insights")
            
        logger.info(f"Initialized Heroku Insights Service with model: {self.model_id}")

    async def get_ai_insights(self, time_range: str = "week") -> Dict[str, Any]:
        """
        Get AI-generated insights on health alerts using Heroku Agents API.
        
        Args:
            time_range: Time period to analyze ("day", "week", "month")
            
        Returns:
            Dict containing AI insights
        """
        cache_key = f"insights:{time_range}"
        
        # Check if we have cached insights
        if cache_key in insights_cache:
            cached_data, timestamp = insights_cache[cache_key]
            # If cache is still valid (within TTL)
            if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
                logger.info(f"Using cached insights for {time_range}")
                return cached_data
        
        logger.info(f"Generating new AI insights for time range: {time_range}")
        
        try:
            # Ensure we have all required configuration
            if not all([self.api_key, self.app_name]):
                logger.error("Missing required configuration for AI insights")
                return self._get_fallback_insights()
            
            # Generate insights using Heroku Agents API
            insights = await self._query_heroku_agent(time_range)
            
            # Cache the results
            insights_cache[cache_key] = (insights, datetime.now())
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            logger.debug(traceback.format_exc())
            return self._get_fallback_insights()

    async def _query_heroku_agent(self, time_range: str) -> Dict[str, Any]:
        """
        Query the Heroku Agents API with postgres tool to analyze database.
        
        Args:
            time_range: Time period to analyze ("day", "week", "month")
            
        Returns:
            Dict containing AI insights
        """
        # Check if we're ready to run queries with the Heroku Agents API
        if not self.using_standard_db:
            logger.warning("Standard database is required for Heroku Agents API. Using fallback insights.")
            return self._get_fallback_insights_with_error("Standard database plan (Standard-0 or higher) is required for Heroku Agents API.")
            
        # Even with a Standard database, we need a follower database for the Agents API
        if not self.is_follower_db:
            logger.warning("Database is not a follower/replica. Heroku Agents API may reject the query.")
            # We'll try anyway, and let the error handling catch any issues
        # Define time window based on time_range
        if time_range == "day":
            time_window = "24 hours"
        elif time_range == "month":
            time_window = "30 days"
        else:  # Default to week
            time_window = "7 days"
        
        # Define the user prompt for insights generation
        prompt = f"""
        You are a Salesforce Health Analyzer specialized in analyzing health alert data.
        
        Please analyze the health alerts from the last {time_window} and provide 3 key insights:
        
        1. Alert Pattern Detected: Identify any patterns or clusters in the alerts, such as 
           increases/decreases in specific categories or notable frequency changes.
           
        2. Potential Issue: Based on the alerts, identify a potential underlying issue 
           that may need attention. Look for correlations or common root causes.
           
        3. Suggested Action: Recommend a specific, actionable step that would help 
           address the most critical issues identified.
        
        Format your response as a JSON object with the following structure:
        {{
            "alert_pattern": {{
                "title": "Brief pattern title",
                "description": "Detailed description with numbers and percentages"
            }},
            "potential_issue": {{
                "title": "Brief issue title",
                "description": "Detailed description of the potential issue"
            }},
            "suggested_action": {{
                "title": "Brief action title",
                "description": "Detailed description of the recommended action"
            }},
            "system_health_summary": "One sentence overall system health assessment"
        }}
        """
        
        # Define SQL query based on time_range
        sql_query = f"""
        -- Get alert counts by category and priority over the specified time period
        WITH alert_stats AS (
            SELECT
                category,
                ai_category,
                ai_priority,
                COUNT(*) as count,
                (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM health_alerts WHERE created_at >= NOW() - INTERVAL '{time_window}')) as percentage
            FROM
                health_alerts
            WHERE
                created_at >= NOW() - INTERVAL '{time_window}'
            GROUP BY
                category, ai_category, ai_priority
            ORDER BY
                count DESC
        ),
        -- Get daily alert counts to track trends
        daily_counts AS (
            SELECT
                DATE(created_at) as alert_date,
                category,
                COUNT(*) as count
            FROM
                health_alerts
            WHERE
                created_at >= NOW() - INTERVAL '{time_window}'
            GROUP BY
                DATE(created_at), category
            ORDER BY
                alert_date, category
        ),
        -- Get unresolved critical/high alerts
        critical_alerts AS (
            SELECT
                title,
                description,
                ai_category,
                ai_priority,
                created_at
            FROM
                health_alerts
            WHERE
                created_at >= NOW() - INTERVAL '{time_window}'
                AND ai_priority IN ('critical', 'high')
                AND is_resolved = FALSE
            ORDER BY
                CASE WHEN ai_priority = 'critical' THEN 0 WHEN ai_priority = 'high' THEN 1 ELSE 2 END,
                created_at DESC
            LIMIT 10
        )
        -- Combine all statistics in JSON format
        SELECT
            json_build_object(
                'alert_stats', (SELECT json_agg(alert_stats) FROM alert_stats),
                'daily_trends', (SELECT json_agg(daily_counts) FROM daily_counts),
                'critical_alerts', (SELECT json_agg(critical_alerts) FROM critical_alerts),
                'total_alerts', (SELECT COUNT(*) FROM health_alerts WHERE created_at >= NOW() - INTERVAL '{time_window}'),
                'unresolved_alerts', (SELECT COUNT(*) FROM health_alerts WHERE created_at >= NOW() - INTERVAL '{time_window}' AND is_resolved = FALSE),
                'time_period', '{time_window}'
            ) as alert_data;
        """
        
        # Prepare the request payload for Heroku Agents API
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "tools": [
                {
                    "type": "heroku_tool",
                    "name": "postgres_run_query",
                    "runtime_params": {
                        "target_app_name": self.app_name,
                        "dyno_size": "standard-1x",
                        "tool_params": {
                            "db_attachment": "HEROKU_POSTGRESQL_COBALT"
                        }
                    }
                }
            ]
        }

        # Make the API request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.agents_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60  # 60-second timeout for the agent call
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error from Heroku Agents API: {error_text}")
                    
                    # Check for specific error messages
                    if "Target database is not a replica" in error_text:
                        logger.error("CRITICAL ERROR: The database is not a follower/replica. Must use a follower database.")
                        logger.error("You need to create a follower database with: heroku addons:create heroku-postgresql:standard-0 --app sf-health-dashboard -- --follow DATABASE_URL")
                        
                    return self._get_fallback_insights_with_error("The database is not configured as a follower/replica, which is required by Heroku Agents API")
                
                try:
                    result = await response.json()
                except Exception as e:
                    # Handle non-JSON responses (e.g., text/event-stream)
                    error_text = await response.text()
                    logger.error(f"Failed to parse response as JSON: {str(e)}. Response: {error_text[:200]}...")
                    return self._get_fallback_insights()
                
                # Extract the AI response
                try:
                    ai_response = result["content"][0]["text"]
                    
                    # Try to parse JSON from the AI response
                    # Look for JSON content within the response
                    json_start = ai_response.find('{')
                    json_end = ai_response.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_content = ai_response[json_start:json_end]
                        insights_data = json.loads(json_content)
                        
                        # Add metadata
                        insights_data["generated_at"] = datetime.now().isoformat()
                        insights_data["time_range"] = time_range
                        
                        return insights_data
                    else:
                        logger.error("Could not find JSON content in AI response")
                        return self._get_fallback_insights()
                        
                except (KeyError, IndexError, json.JSONDecodeError) as e:
                    logger.error(f"Error parsing AI response: {str(e)}")
                    return self._get_fallback_insights()

    def _get_fallback_insights_with_error(self, error_message: str = None) -> Dict[str, Any]:
        """
        Return fallback insights with a specific error message.
        
        Args:
            error_message: Specific error message to include in the fallback
            
        Returns:
            Dict containing fallback insights
        """
        description = "The database is not configured as a follower/replica, which is required by Heroku Agents API."
        if error_message:
            description = error_message
            
        return {
            "alert_pattern": {
                "title": "Database configuration error",
                "description": description
            },
            "potential_issue": {
                "title": "Missing follower database",
                "description": "The Heroku Agents API requires a follower/replica database, but the current database is not configured as one."
            },
            "suggested_action": {
                "title": "Create a follower database",
                "description": "Run: heroku addons:create heroku-postgresql:standard-0 --app sf-health-dashboard -- --follow DATABASE_URL"
            },
            "system_health_summary": "AI insights unavailable - database configuration error",
            "generated_at": datetime.now().isoformat(),
            "time_range": "week",  # Default to weekly time range for fallback
            "is_fallback": True
        }
        
    def _get_fallback_insights(self) -> Dict[str, Any]:
        """
        Return generic fallback insights when the AI service is unavailable.
        
        Returns:
            Dict containing fallback insights
        """
        return self._get_fallback_insights_with_error("The AI insights service is temporarily unavailable.")

# Create a singleton instance
heroku_insights_service = HerokuInsightsService()