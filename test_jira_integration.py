import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from models.schemas import HealthAlert, PriorityLevel, HealthCategory
from services.jira_service import JIRAService

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ["JIRA_API_TOKEN", "JIRA_DOMAIN", "JIRA_EMAIL"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please set all required variables before running this test.")
    print("Required environment variables are missing. Check the logs for details.")
    exit(1)

async def test_jira_ticket_creation():
    """Test creating a JIRA ticket for a test alert"""
    
    # Create a test alert
    test_alert = HealthAlert(
        id=999,
        title="Test Alert for JIRA Integration",
        description="This is a test alert to verify JIRA integration functionality.",
        category=HealthCategory.SECURITY,
        source_system="Test Script",
        created_at=datetime.now(),
        ai_category="Security",
        ai_priority=PriorityLevel.HIGH,
        ai_summary="Test alert for JIRA ticket creation verification.",
        ai_recommendation="This is a test alert, please ignore.",
        is_resolved=False,
        jira_ticket_id=None,
        slack_alert_sent=False
    )
    
    logger.info(f"Creating JIRA ticket for test alert: {test_alert.title}")
    
    # Create JIRA service
    jira_service = JIRAService()
    
    # Try to create a ticket
    ticket_id = await jira_service.create_ticket(test_alert)
    
    if ticket_id:
        logger.info(f"✅ Successfully created JIRA ticket: {ticket_id}")
        ticket_url = await jira_service.get_ticket_url(ticket_id)
        print(f"Test successful! Created JIRA ticket: {ticket_id}")
        print(f"View ticket at: {ticket_url}")
    else:
        logger.error("❌ Failed to create JIRA ticket")
        print("Test failed. Check the logs for details.")

async def test_jira_service_validation():
    """Test JIRA service validation"""
    
    jira_service = JIRAService()
    
    # Validate credentials
    if jira_service._validate_credentials():
        logger.info("✅ JIRA credentials validation successful")
        print("JIRA credentials validation passed!")
    else:
        logger.error("❌ JIRA credentials validation failed")
        print("JIRA credentials validation failed. Check the logs for details.")

async def main():
    """Run all tests"""
    print("Running JIRA integration tests...")
    
    # First check credentials
    await test_jira_service_validation()
    print("")
    
    # If credentials are valid, create a test ticket
    await test_jira_ticket_creation()
    
if __name__ == "__main__":
    asyncio.run(main())