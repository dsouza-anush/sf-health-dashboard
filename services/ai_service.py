import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.heroku import HerokuProvider

from models.schemas import HealthAlertCategorization, HealthAlert

load_dotenv()

# Get API key from environment - try both naming conventions
INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY") or os.getenv("HEROKU_INFERENCE_API_KEY")

# Initialize the Claude model with Heroku provider
model = OpenAIModel(
    'claude-4-sonnet',
    provider=HerokuProvider(api_key=INFERENCE_API_KEY),
)

# Create a Pydantic AI agent
health_agent = Agent(model)

async def categorize_health_alert(alert: HealthAlert) -> HealthAlertCategorization:
    """
    Categorize a health alert using Claude AI on Heroku.
    
    This function sends the health alert data to Claude for analysis
    and returns a categorization with priority, summary, and recommended actions.
    """
    
    # Create a system prompt for the AI
    system_prompt = """
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
    
    # Create a user prompt with the alert details
    user_prompt = f"""
    Health Alert Details:
    
    Title: {alert.title}
    Description: {alert.description}
    Source System: {alert.source_system}
    Category: {alert.category}
    Raw Data: {alert.raw_data if alert.raw_data else "None provided"}
    """
    
    # Get categorization from the AI agent
    result = await health_agent.run(
        HealthAlertCategorization, 
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    return result