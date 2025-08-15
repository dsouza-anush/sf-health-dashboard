import os
import logging
import base64
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from models.schemas import HealthAlert

# Set up logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get JIRA credentials from environment
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SF")

class JIRAService:
    """Service for interacting with the JIRA API"""
    
    def __init__(self):
        """Initialize the JIRA service with credentials from environment variables"""
        self.api_token = JIRA_API_TOKEN
        self.domain = JIRA_DOMAIN
        self.email = JIRA_EMAIL
        self.project_key = JIRA_PROJECT_KEY
        
        # Create basic auth header
        if self.email and self.api_token:
            auth_str = f"{self.email}:{self.api_token}"
            self.auth_header = f"Basic {base64.b64encode(auth_str.encode()).decode()}"
        else:
            self.auth_header = None
            
    def _validate_credentials(self) -> bool:
        """Validate that all required credentials are available"""
        if not self.api_token:
            logger.error("JIRA_API_TOKEN is not set")
            return False
        if not self.domain:
            logger.error("JIRA_DOMAIN is not set")
            return False
        if not self.email:
            logger.error("JIRA_EMAIL is not set")
            return False
        if not self.project_key:
            logger.warning("JIRA_PROJECT_KEY is not set, using default 'SF'")
        return True
    
    async def create_ticket(self, alert: HealthAlert) -> Optional[str]:
        """
        Create a JIRA ticket for a health alert
        
        Args:
            alert: The health alert to create a ticket for
            
        Returns:
            str: The ID of the created JIRA ticket, or None if creation failed
        """
        # Validate credentials
        if not self._validate_credentials() or not self.auth_header:
            logger.error("Missing JIRA credentials, cannot create ticket")
            return None
        
        # Build the ticket data
        priority_map = {
            "critical": "Highest",
            "high": "High",
            "medium": "Medium",
            "low": "Low"
        }
        
        # Get priority from alert, defaulting to "Medium" if not available
        priority_name = priority_map.get(
            alert.ai_priority.value if alert.ai_priority else "medium", 
            "Medium"
        )
        
        # Build labels from alert data
        labels = [
            f"category_{alert.category.value}",
            f"source_{alert.source_system.lower().replace(' ', '_')}"
        ]
        
        if alert.ai_category:
            labels.append(f"ai_category_{alert.ai_category.lower().replace(' ', '_')}")
        
        if alert.ai_priority:
            labels.append(f"priority_{alert.ai_priority.value}")
        
        # Build the description including AI analysis if available
        description = f"{alert.description}\n\n"
        
        if alert.raw_data:
            description += f"*Raw Data:*\n{{code}}\n{alert.raw_data}\n{{code}}\n\n"
        
        description += f"*Source System:* {alert.source_system}\n"
        description += f"*Alert ID:* {alert.id}\n"
        
        if alert.ai_category:
            description += "\nh2. AI Analysis\n\n"
            description += f"*Category:* {alert.ai_category}\n"
            description += f"*Priority:* {alert.ai_priority.value if alert.ai_priority else 'Not set'}\n"
            
            if alert.ai_summary:
                description += f"\n*Summary:*\n{alert.ai_summary}\n"
            
            if alert.ai_recommendation:
                description += f"\n*Recommendation:*\n{alert.ai_recommendation}\n"
                
        # Add link back to alert in the dashboard
        app_host = os.getenv('APP_HOST', 'localhost:8000')
        description += f"\n[View Alert in Dashboard|http://{app_host}/alert/{alert.id}]"
        
        # Build the ticket payload
        ticket_data = {
            "fields": {
                "project": {
                    "key": self.project_key
                },
                "summary": f"{alert.title}",
                "description": description,
                "issuetype": {
                    "name": "Bug"
                },
                "priority": {
                    "name": priority_name
                },
                "labels": labels
            }
        }
        
        # Send the request to JIRA
        try:
            client = httpx.AsyncClient()
            response = await client.post(
                f"{self.domain}/rest/api/2/issue",
                json=ticket_data,
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            ticket_key = result.get("key")
            if ticket_key:
                logger.info(f"Created JIRA ticket {ticket_key} for alert {alert.id}")
                return ticket_key
            else:
                logger.error(f"Failed to get ticket key from JIRA response: {result}")
                return None
                
        except httpx.HTTPStatusError as e:
            logger.error(f"JIRA API error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating JIRA ticket: {str(e)}")
            return None
            
    async def get_ticket_url(self, ticket_key: str) -> str:
        """
        Get the URL for a JIRA ticket
        
        Args:
            ticket_key: The JIRA ticket key
            
        Returns:
            str: The URL for the ticket
        """
        if not self.domain:
            return f"JIRA ticket: {ticket_key}"
            
        return f"{self.domain}/browse/{ticket_key}"