import os
import json
import asyncio
import traceback
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.heroku import HerokuProvider

from models.schemas import HealthAlertCategorization, HealthAlert

# Set up logger
logger = logging.getLogger(__name__)

load_dotenv()

# Get API key from environment - check all possible variable names
INFERENCE_API_KEY = os.getenv("HEROKU_INFERENCE_API_KEY") or os.getenv("INFERENCE_API_KEY") or os.getenv("INFERENCE_KEY")

# Get model ID and URL from environment
INFERENCE_MODEL_ID = os.getenv("INFERENCE_MODEL_ID", "claude-4-sonnet")
INFERENCE_URL = os.getenv("INFERENCE_URL", "https://us.inference.heroku.com")

if not INFERENCE_API_KEY:
    logger.warning("No inference API key found. AI categorization will not work.")
    # Will fall back to default categorization
else:
    logger.info(f"Using model: {INFERENCE_MODEL_ID} with Heroku AI")

# Health analyzer prompt instructions
HEALTH_ANALYZER_INSTRUCTIONS = """
You are a Salesforce Health Analyzer specialized in categorizing health alerts.

Analyze the health alert details carefully and provide:
1. A category - select the MOST appropriate one from the provided list based on the alert details
2. A priority level (low, medium, high, or critical) based on the potential business impact
3. A concise summary of the issue (1-2 sentences maximum)
4. A specific, actionable recommendation to resolve the issue

CATEGORIES (CHOOSE ONE):
- Configuration: System setup issues, organization settings, workflow rules
- Security: Vulnerabilities, permission issues, access control problems
- Performance: System performance, response times, throughput issues
- Data: Data integrity, storage limits, data quality issues
- Integration: Problems with external systems, API calls, data flows
- Compliance: Regulatory or policy violations
- Code: Problems in custom code, Apex triggers, or scripting
- User Experience: Interface issues affecting users

PRIORITY GUIDELINES:
- critical: Immediate action required; business operations severely impacted
- high: Urgent attention needed; significant impact on business functions
- medium: Important but not urgent; moderate impact on specific functions
- low: Minor issue with limited impact; can be addressed during routine maintenance

Your output must be specific, concrete and directly related to the alert details. Avoid generic responses.
"""

# Define possible categories for the emergency fallback system
CATEGORIES = [
    "Configuration", 
    "Security", 
    "Performance", 
    "Data", 
    "Integration", 
    "Compliance", 
    "Code", 
    "User Experience"
]

# Define possible priorities
PRIORITIES = ["low", "medium", "high", "critical"]

# Initialize the model and agent with simpler configuration
agent = None
try:
    if INFERENCE_API_KEY:
        # Initialize Claude model with Heroku provider
        model = OpenAIModel(
            INFERENCE_MODEL_ID,
            provider=HerokuProvider(
                api_key=INFERENCE_API_KEY,
                base_url=INFERENCE_URL
            )
        )
        
        # Create a simple agent without complex parameters
        agent = Agent(model, instructions=HEALTH_ANALYZER_INSTRUCTIONS)
        logger.info("AI agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AI agent: {str(e)}")
    logger.debug(traceback.format_exc())
    # Don't crash the app if AI initialization fails
    logger.info("Continuing with fallback categorization")


def get_default_categorization(error_message: Optional[str] = None) -> HealthAlertCategorization:
    """Returns a default categorization when AI is unavailable or fails"""
    summary = "AI categorization unavailable"
    if error_message:
        summary += f". Error: {error_message}"
        logger.warning(f"Using default categorization due to error: {error_message}")
        
    return HealthAlertCategorization(
        category="Configuration",  
        priority="medium",
        summary=summary,
        recommendation="Please configure the AI service with a valid API key"
    )

# Define category-specific fallbacks
DEFAULT_CATEGORIZATIONS = {
    "security": HealthAlertCategorization(
        category="Security", priority="high",
        summary="Security alert requiring immediate attention.",
        recommendation="Review security settings and recent changes."
    ),
    "limits": HealthAlertCategorization(
        category="Data", priority="medium",
        summary="System approaching defined resource limits.",
        recommendation="Review resource usage and optimize configurations."
    ),
    "exceptions": HealthAlertCategorization(
        category="Code", priority="medium",
        summary="Application code exceptions detected.",
        recommendation="Debug error logs and fix application issues."
    )
}

async def categorize_health_alert(alert: HealthAlert) -> HealthAlertCategorization:
    """
    Categorize a health alert using Claude AI.
    
    This function sends the health alert data to Claude for analysis
    and returns a categorization with priority, summary, and recommended actions.
    
    If the AI service is unavailable, returns a default categorization.
    """
    if not agent:
        logger.warning("AI agent not initialized - using default categorization")
        # Use category-specific fallback if available
        if alert.category in DEFAULT_CATEGORIZATIONS:
            return DEFAULT_CATEGORIZATIONS[alert.category]
        return get_default_categorization("AI agent not available")
    
    logger.info(f"Categorizing alert: {getattr(alert, 'id', 'new')} - {alert.title}")
    
    # Format the alert details for the user prompt
    user_message = f"""
    Health Alert Details:
    
    Title: {alert.title}
    Description: {alert.description}
    Source System: {alert.source_system}
    Category (from monitoring system): {alert.category}
    Raw Data: {alert.raw_data if alert.raw_data else "None provided"}
    
    Based on these alert details, please provide a detailed analysis using this format:
    **Category:** [Choose one category]
    **Priority:** [low, medium, high, or critical]
    **Summary:** [1-2 sentence summary]
    **Recommendation:** [specific action to take]
    """
    
    try:
        # Set a timeout for the API call to prevent hanging
        try:
                # Call the AI agent with timeout handling
            raw_result = await asyncio.wait_for(agent.run(user_message), timeout=30.0)
            logger.debug(f"AI response received: {raw_result}")
            
            # Convert the result to the expected format
            if isinstance(raw_result, dict):
                result = HealthAlertCategorization(
                    category=raw_result.get('category', 'Configuration'),
                    priority=raw_result.get('priority', 'medium'),
                    summary=raw_result.get('summary', 'Analysis completed.'),
                    recommendation=raw_result.get('recommendation', 'Review alert details.')
                )
                return result
            elif hasattr(raw_result, 'output'):  # Handle AgentRunResult object
                logger.info("Processing AgentRunResult object")
                try:
                    # Extract key fields using regex
                    import re
                    result_text = raw_result.output
                    
                    # Extract fields using regex patterns
                    category_match = re.search(r'\*\*Category:\*\*\s*(\w+)', result_text, re.IGNORECASE)
                    priority_match = re.search(r'\*\*Priority:\*\*\s*(\w+)', result_text, re.IGNORECASE)
                    summary_match = re.search(r'\*\*Summary:\*\*\s*([^\n]+)', result_text, re.IGNORECASE)
                    recommendation_match = re.search(r'\*\*Recommendation:\*\*\s*([^\n]+)', result_text, re.IGNORECASE)
                    
                    category = category_match.group(1) if category_match else "Configuration"
                    priority = priority_match.group(1) if priority_match else "medium"
                    summary = summary_match.group(1) if summary_match else "Analysis completed."
                    recommendation = recommendation_match.group(1) if recommendation_match else "Review alert details."
                    
                    logger.info(f"Extracted fields - Category: {category}, Priority: {priority}")
                    
                    return HealthAlertCategorization(
                        category=category,
                        priority=priority,
                        summary=summary,
                        recommendation=recommendation
                    )
                except Exception as e:
                    logger.error(f"Error parsing AgentRunResult: {str(e)}")
                    return get_default_categorization(f"Error parsing response: {str(e)}")
            elif isinstance(raw_result, str):
                # Handle string response by extracting JSON if possible
                try:
                    json_data = json.loads(raw_result)
                    return HealthAlertCategorization(
                        category=json_data.get('category', 'Configuration'),
                        priority=json_data.get('priority', 'medium'),
                        summary=json_data.get('summary', 'Analysis completed.'),
                        recommendation=json_data.get('recommendation', 'Review alert details.')
                    )
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse string response as JSON: {raw_result[:100]}...")
                    # If not valid JSON, use default with raw response as summary
                    return HealthAlertCategorization(
                        category="Configuration",
                        priority="medium",
                        summary=raw_result[:200] if len(raw_result) > 200 else raw_result,
                        recommendation="Review alert details and take appropriate action."
                    )
            else:
                # Unexpected response format
                logger.error(f"Unexpected response type: {type(raw_result)}")
                # Use category-specific fallback if available
                if alert.category in DEFAULT_CATEGORIZATIONS:
                    return DEFAULT_CATEGORIZATIONS[alert.category]
                return get_default_categorization(f"Unexpected response type: {type(raw_result)}")
            
        except asyncio.TimeoutError:
            logger.warning("AI request timed out after 30 seconds")
            # Use category-specific fallback if available
            if alert.category in DEFAULT_CATEGORIZATIONS:
                return DEFAULT_CATEGORIZATIONS[alert.category]
            return get_default_categorization("Request timed out")
    except Exception as e:
        logger.error(f"Error in AI categorization: {str(e)}")
        logger.debug(traceback.format_exc())
        # Use category-specific fallback if available
        if alert.category in DEFAULT_CATEGORIZATIONS:
            return DEFAULT_CATEGORIZATIONS[alert.category]
        return get_default_categorization(f"Error: {str(e)[:100]}")

