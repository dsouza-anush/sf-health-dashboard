import os
import logging
import httpx
from typing import Any, Dict, List
from dotenv import load_dotenv
from models.schemas import HealthAlert, PriorityLevel

# Set up logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Slack API key from environment
SLACK_API_KEY = os.getenv("SLACK_API_KEY")
SLACK_ALERTS_CHANNEL = os.getenv("SLACK_ALERTS_CHANNEL", "#sf-health-alerts")

async def send_slack_message(channel: str, blocks: List[Dict[str, Any]]) -> bool:
    """
    Sends a message to a Slack channel using blocks format.
    
    Args:
        channel: The Slack channel to send the message to
        blocks: A list of Slack blocks to send
    
    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    if not SLACK_API_KEY:
        logger.error("SLACK_API_KEY is not set, cannot send Slack notification")
        return False
        
    try:
        client = httpx.AsyncClient()
        response = await client.post(
            'https://slack.com/api/chat.postMessage',
            json={
                'channel': channel,
                'blocks': blocks,
            },
            headers={
                'Authorization': f'Bearer {SLACK_API_KEY}',
                'Content-Type': 'application/json'
            },
            timeout=5.0
        )
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get('ok', False):
            error = result.get('error', 'Unknown error')
            logger.error(f"Failed to send to Slack: {error}")
            return False
            
        logger.info(f"Successfully sent alert to Slack channel {channel}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending message to Slack: {str(e)}")
        return False

def format_alert_for_slack(alert: HealthAlert) -> List[Dict[str, Any]]:
    """
    Formats a health alert into Slack message blocks.
    
    Args:
        alert: The health alert to format
    
    Returns:
        List[Dict[str, Any]]: A list of Slack blocks
    """
    # Determine color based on priority
    color = "#ff0000"  # Default red for high/critical
    if alert.ai_priority == PriorityLevel.HIGH:
        color = "#ff9900"  # Orange for high
    elif alert.ai_priority == PriorityLevel.CRITICAL:
        color = "#ff0000"  # Red for critical
        
    # Create blocks for the message
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 {alert.ai_priority.upper()} ALERT: {alert.title}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*ID:* {alert.id}\n*Category:* {alert.category}\n*AI Category:* {alert.ai_category}\n*Priority:* {alert.ai_priority}\n*Source:* {alert.source_system}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n{alert.description}"
            }
        }
    ]
    
    # Add AI summary and recommendation if available
    if alert.ai_summary:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*AI Summary:*\n{alert.ai_summary}"
            }
        })
        
    if alert.ai_recommendation:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Recommendation:*\n{alert.ai_recommendation}"
            }
        })
    
    # Add link to dashboard
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"<http://{os.getenv('APP_HOST', 'localhost:8000')}/alert/{alert.id}|View Alert Details>"
        }
    })
    
    return blocks

async def send_alert_notification(alert: HealthAlert) -> bool:
    """
    Sends a notification to Slack for a high or critical priority alert.
    
    Args:
        alert: The health alert to send
        
    Returns:
        bool: True if the notification was sent successfully, False otherwise
    """
    # Only send notifications for high or critical priority alerts
    if alert.ai_priority not in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]:
        logger.debug(f"Alert {alert.id} priority {alert.ai_priority} doesn't meet notification threshold")
        return False
        
    # Don't send duplicate notifications
    if alert.slack_alert_sent:
        logger.debug(f"Alert {alert.id} already sent to Slack")
        return False
    
    # Format the alert message
    blocks = format_alert_for_slack(alert)
    
    # Send to Slack
    return await send_slack_message(SLACK_ALERTS_CHANNEL, blocks)