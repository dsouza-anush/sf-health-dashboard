import os
import json
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.heroku import HerokuProvider

from models.schemas import HealthAlertCategorization, HealthAlert

load_dotenv()

# Get API key from environment - check all possible variable names
INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY") or os.getenv("INFERENCE_KEY") or os.getenv("HEROKU_INFERENCE_API_KEY")

if not INFERENCE_API_KEY:
    print("WARNING: No inference API key found. AI categorization will not work.")

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

# Initialize the Claude model with Heroku provider
model = None
if INFERENCE_API_KEY:
    model = OpenAIModel(
        'claude-4-sonnet',
        provider=HerokuProvider(api_key=INFERENCE_API_KEY)
    )

# Define a simplified manual schema that Claude can handle
SIMPLIFIED_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "description": "The most appropriate category for this health alert"
        },
        "priority": {
            "type": "string",
            "description": "The priority level for this health alert",
            "enum": ["low", "medium", "high", "critical"]
        },
        "summary": {
            "type": "string",
            "description": "A concise summary of the health alert"
        },
        "recommendation": {
            "type": "string",
            "description": "A recommended action to resolve the health alert"
        }
    },
    "required": ["category", "priority", "summary", "recommendation"]
}

# Create a properly configured Pydantic AI agent with manual schema
health_agent = None
if model:
    health_agent = Agent(
        model,
        output_schema=SIMPLIFIED_SCHEMA,  # Use our manually defined schema instead of output_type
        instructions=HEALTH_ANALYZER_INSTRUCTIONS
    )

def get_default_categorization(error_message: Optional[str] = None) -> HealthAlertCategorization:
    """Returns a default categorization when AI is unavailable or fails"""
    summary = "AI categorization unavailable - default category assigned"
    if error_message:
        summary += f". Error: {error_message}"
        
    return HealthAlertCategorization(
        category="Configuration",  
        priority="medium",
        summary=summary,
        recommendation="Please configure the AI service with a valid API key"
    )

async def categorize_health_alert(alert: HealthAlert) -> HealthAlertCategorization:
    """
    Categorize a health alert using Claude AI on Heroku.
    
    This function sends the health alert data to Claude for analysis
    and returns a categorization with priority, summary, and recommended actions.
    
    If the AI service is unavailable, returns a default categorization.
    """
    if not health_agent:
        return get_default_categorization()
    
    # Format the alert details for the user prompt with more context
    user_message = f"""
    Health Alert Details:
    
    Title: {alert.title}
    Description: {alert.description}
    Source System: {alert.source_system}
    Category (from monitoring system): {alert.category}
    Raw Data: {alert.raw_data if alert.raw_data else "None provided"}
    
    Based on these alert details, please provide a detailed analysis.
    """
    
    try:
        # Set a timeout for the API call to prevent hanging
        try:
            # Get categorization from the AI agent with timeout handling
            result_dict = await asyncio.wait_for(health_agent.run(user_message), timeout=30.0)
            print(f"AI Service response received: {result_dict}")
            
            # Convert the raw dict to our Pydantic model
            try:
                # Try to parse the result into our Pydantic model
                result = HealthAlertCategorization(
                    category=result_dict.get('category', 'Configuration'),
                    priority=result_dict.get('priority', 'medium'),
                    summary=result_dict.get('summary', 'AI analysis completed but produced incomplete results.'),
                    recommendation=result_dict.get('recommendation', 'Review the alert details manually for appropriate action.')
                )
                return result
            except Exception as parsing_error:
                print(f"Error parsing AI result: {parsing_error}")
                print(f"Raw AI result: {result_dict}")
                return get_default_categorization(f"Error parsing result: {str(parsing_error)}")
        except asyncio.TimeoutError:
            print("AI categorization timed out after 30 seconds")
            return get_default_categorization("Request timed out after 30 seconds")
    except Exception as e:
        print(f"Error in AI categorization: {str(e)}")
        return get_default_categorization(str(e))