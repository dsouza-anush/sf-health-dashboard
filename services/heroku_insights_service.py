import os
import json
import logging
import traceback
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HerokuInsightsService:
    """
    Service for generating AI insights on health alerts using the Heroku Agents API.
    
    This service connects to the Heroku Agents API to analyze health alerts
    and provide AI-generated insights.
    """
    
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
            
        # Check database configuration
        self.using_standard_db = True  # We assume Standard DB for Heroku
        self.fork_follow_available = True  # COBALT is a follower database
        
        # Log database information
        logger.info(f"Using follower database '{self.db_attachment}' for AI insights")
    
    async def get_ai_insights(self, time_range: str) -> Dict[str, Any]:
        """
        Get AI-generated insights on health alerts for the specified time range.
        
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
        
        # Let Claude generate the appropriate SQL query based on the prompt
        
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

        # Make the API request using streaming response handling for SSE
        try:
            logger.info(f"Making request to Heroku Agents API endpoint: {self.agents_endpoint}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.agents_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    },
                    json=payload,
                    timeout=120  # Increased timeout for the agent call (2 minutes)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from Heroku Agents API: {error_text}")
                        
                        # Check for specific error messages
                        if "Target database is not a replica" in error_text:
                            logger.error("CRITICAL ERROR: The database is not a follower/replica. Must use a follower database.")
                            logger.error("You need to create a follower database with: heroku addons:create heroku-postgresql:standard-0 --app sf-health-dashboard -- --follow DATABASE_URL")
                            
                        return self._get_fallback_insights_with_error("The database is not configured as a follower/replica, which is required by Heroku Agents API")
                    
                    # Process the event stream response
                    last_ai_text = ""
                    content_type = response.headers.get("Content-Type", "")
                    logger.info(f"Response content type: {content_type}")
                    
                    # Handle SSE (Server-Sent Events) response
                    if "text/event-stream" in content_type:
                        try:
                            # Process SSE stream according to the actual format
                            final_message = None
                            
                            # Read the entire response content
                            content = await response.read()
                            content_str = content.decode('utf-8')
                            
                            # Split into events based on double newlines
                            events = content_str.strip().split('\n\n')
                            
                            for event_block in events:
                                if not event_block.strip():
                                    continue
                                    
                                lines = event_block.strip().split('\n')
                                event_type = None
                                event_data = None
                                
                                # Parse event type and data
                                for line in lines:
                                    if line.startswith('event:'):
                                        event_type = line[6:].strip()
                                    elif line.startswith('data:'):
                                        event_data = line[5:].strip()
                                
                                # Process message events
                                if event_type == "message" and event_data:
                                    try:
                                        data = json.loads(event_data)
                                        
                                        # Look for chat completion with stop reason
                                        if (data.get("object") == "chat.completion" and 
                                            data.get("choices")):
                                            
                                            for choice in data["choices"]:
                                                if (choice.get("finish_reason") == "stop" and 
                                                    choice.get("message", {}).get("content")):
                                                    final_message = choice["message"]["content"]
                                                    logger.info(f"Found final completion message: {len(final_message)} chars")
                                                    break
                                                    
                                    except json.JSONDecodeError as e:
                                        logger.debug(f"Invalid JSON in event data: {e}")
                                        logger.debug(f"Event data: {event_data[:200]}...")
                                        continue
                                        
                                elif event_type == "done":
                                    logger.info("Received done event, stream complete")
                                    break
                            
                            # Use the final completion message as our AI text
                            if final_message:
                                last_ai_text = final_message
                                logger.info("Successfully extracted AI response from SSE stream")
                            else:
                                logger.warning("Processed entire SSE stream but didn't find a final completion message")
                                
                        except Exception as e:
                            logger.error(f"Error processing event stream: {str(e)}")
                            logger.debug(traceback.format_exc())
                            return self._get_fallback_insights()
                    else:
                        # Try standard JSON response as fallback
                        try:
                            result = await response.json()
                            if "choices" in result:
                                for choice in result.get("choices", []):
                                    if choice.get("message", {}).get("content"):
                                        last_ai_text = choice["message"]["content"]
                                        break
                        except Exception as e:
                            logger.error(f"Failed to parse response as JSON: {str(e)}")
                            error_text = await response.text()
                            logger.debug(f"Response: {error_text[:200]}...")
                            return self._get_fallback_insights()

            # Extract insights from the AI text response
            try:
                if last_ai_text:
                    # Try to parse JSON from the AI response
                    # First attempt to parse the entire response as JSON
                    try:
                        # Try direct JSON parsing first
                        insights_data = json.loads(last_ai_text)
                        
                        # Add metadata
                        insights_data["generated_at"] = datetime.now().isoformat()
                        insights_data["time_range"] = time_range
                        insights_data["is_fallback"] = False
                        
                        return insights_data
                    except json.JSONDecodeError:
                        # If direct parsing fails, look for JSON content within the response
                        json_start = last_ai_text.find('{')
                        json_end = last_ai_text.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_content = last_ai_text[json_start:json_end]
                            try:
                                insights_data = json.loads(json_content)
                                
                                # Add metadata
                                insights_data["generated_at"] = datetime.now().isoformat()
                                insights_data["time_range"] = time_range
                                insights_data["is_fallback"] = False
                                
                                return insights_data
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON from AI response: {str(e)}")
                                logger.debug(f"JSON content attempted to parse: {json_content}")
                                return self._get_fallback_insights()
                        else:
                            logger.error("Could not find JSON content in AI response")
                            logger.debug(f"AI response received: {last_ai_text[:200]}...")
                            return self._get_fallback_insights()
                else:
                    logger.error("No AI text response was extracted from the Heroku Agents API")
                    return self._get_fallback_insights()
            except Exception as e:
                logger.error(f"Error processing AI response: {str(e)}")
                logger.debug(traceback.format_exc())
                return self._get_fallback_insights()
        except Exception as e:
            logger.error(f"Error connecting to Heroku Agents API: {str(e)}")
            logger.debug(traceback.format_exc())
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
                "description": "The AI insights service is temporarily unavailable."
            },
            "potential_issue": {
                "title": "Missing follower database",
                "description": description
            },
            "suggested_action": {
                "title": "Create a follower database",
                "description": "Run: heroku addons:create heroku-postgresql:standard-0 --app sf-health-dashboard -- --follow DATABASE_URL"
            },
            "system_health_summary": "AI insights unavailable - database configuration error",
            "generated_at": datetime.now().isoformat(),
            "time_range": "week",
            "is_fallback": True
        }
    
    def _get_fallback_insights(self) -> Dict[str, Any]:
        """
        Return fallback insights for when the AI service is unavailable.
        
        Returns:
            Dict containing fallback insights
        """
        return self._get_fallback_insights_with_error("The AI insights service is temporarily unavailable.")


# Initialize the service as a global instance
heroku_insights_service = HerokuInsightsService()