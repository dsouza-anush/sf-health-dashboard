import os
from typing import Optional
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

Analyze the health alert and provide:
1. A category - choose the most appropriate one based on the alert details
2. A priority level (low, medium, high, or critical) based on the potential impact
3. A concise summary of the issue
4. A recommended action to resolve the issue

Categories to choose from:
- Performance: Issues related to system performance, response times, etc.
- Security: Security vulnerabilities, permission issues, access control problems
- Data: Issues with data integrity, storage, limits, etc.
- Integration: Problems with external systems, APIs, data flows
- Compliance: Regulatory or policy violations
- Configuration: System setup issues, organization settings
- Code: Problems in custom code, Apex triggers, etc.
- User Experience: Interface issues affecting users

Ensure your recommendations are specific, actionable, and appropriate for the severity.
"""

# Initialize the Claude model with Heroku provider
model = None
if INFERENCE_API_KEY:
    model = OpenAIModel(
        'claude-4-sonnet',
        provider=HerokuProvider(api_key=INFERENCE_API_KEY),
        model_kwargs={
            "temperature": 0.2,  # Lower temperature for more consistent categorization
            "max_tokens": 1000,
        }
    )

# Create a properly configured Pydantic AI agent
health_agent = None
if model:
    health_agent = Agent(
        model,
        output_type=HealthAlertCategorization,
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
    
    # Format the alert details for the user prompt
    user_message = f"""
    Health Alert Details:
    
    Title: {alert.title}
    Description: {alert.description}
    Source System: {alert.source_system}
    Category: {alert.category}
    Raw Data: {alert.raw_data if alert.raw_data else "None provided"}
    """
    
    try:
        # Get categorization from the AI agent with proper error handling
        result = await health_agent.run(user_message)
        return result
    except Exception as e:
        print(f"Error in AI categorization: {str(e)}")
        return get_default_categorization(str(e))