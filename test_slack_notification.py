import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from models.schemas import HealthAlert, PriorityLevel, HealthCategory
from services.slack_service import send_alert_notification

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required environment variables
if not os.getenv("SLACK_API_KEY"):
    logger.error("SLACK_API_KEY environment variable is not set")
    print("Please set the SLACK_API_KEY environment variable")
    exit(1)

async def test_slack_notification():
    """Test sending a high priority alert to Slack"""
    
    # Create a test alert
    test_alert = HealthAlert(
        id=999,
        title="Test High Priority Alert",
        description="This is a test alert to verify Slack integration functionality.",
        category=HealthCategory.SECURITY,
        source_system="Test Script",
        created_at=datetime.now(),
        ai_category="Security",
        ai_priority=PriorityLevel.HIGH,
        ai_summary="Test alert for Slack notification verification.",
        ai_recommendation="This is just a test, no action required.",
        is_resolved=False,
        slack_alert_sent=False
    )
    
    logger.info(f"Sending test alert to Slack: {test_alert.title}")
    
    # Send the alert to Slack
    result = await send_alert_notification(test_alert)
    
    if result:
        logger.info("✅ Successfully sent test alert to Slack!")
        print("Test successful! Check your Slack channel for the alert.")
    else:
        logger.error("❌ Failed to send test alert to Slack")
        print("Test failed. Check the logs for details.")

async def test_critical_alert():
    """Test sending a critical priority alert to Slack"""
    
    # Create a test critical alert
    test_alert = HealthAlert(
        id=1000,
        title="Test CRITICAL Priority Alert",
        description="This is a test CRITICAL alert to verify Slack integration functionality.",
        category=HealthCategory.EXCEPTIONS,
        source_system="Test Script",
        created_at=datetime.now(),
        ai_category="Code",
        ai_priority=PriorityLevel.CRITICAL,
        ai_summary="Critical issue detected requiring immediate attention.",
        ai_recommendation="Immediate action required: Review system logs and take appropriate action.",
        is_resolved=False,
        slack_alert_sent=False
    )
    
    logger.info(f"Sending critical test alert to Slack: {test_alert.title}")
    
    # Send the alert to Slack
    result = await send_alert_notification(test_alert)
    
    if result:
        logger.info("✅ Successfully sent critical test alert to Slack!")
        print("Test successful! Check your Slack channel for the critical alert.")
    else:
        logger.error("❌ Failed to send critical test alert to Slack")
        print("Test failed. Check the logs for details.")

async def test_medium_priority_alert():
    """Test that medium priority alerts are NOT sent to Slack"""
    
    # Create a test medium priority alert
    test_alert = HealthAlert(
        id=1001,
        title="Test Medium Priority Alert",
        description="This is a medium priority alert that should NOT be sent to Slack.",
        category=HealthCategory.EVENT,
        source_system="Test Script",
        created_at=datetime.now(),
        ai_category="Performance",
        ai_priority=PriorityLevel.MEDIUM,
        ai_summary="Medium priority issue detected.",
        ai_recommendation="Review during regular maintenance.",
        is_resolved=False,
        slack_alert_sent=False
    )
    
    logger.info(f"Attempting to send medium priority alert to Slack (should be skipped): {test_alert.title}")
    
    # This should return False as medium priority alerts should be skipped
    result = await send_alert_notification(test_alert)
    
    if not result:
        logger.info("✅ Correctly skipped sending medium priority alert to Slack")
        print("Test successful! Medium priority alert was correctly not sent to Slack.")
    else:
        logger.error("❌ Medium priority alert was incorrectly sent to Slack")
        print("Test failed. Medium priority alerts should not be sent to Slack.")

async def main():
    """Run all tests"""
    print("Running Slack notification tests...")
    
    # Run tests
    await test_slack_notification()
    print("")
    await test_critical_alert()
    print("")
    await test_medium_priority_alert()
    
if __name__ == "__main__":
    asyncio.run(main())