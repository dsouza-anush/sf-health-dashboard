import logging
from sqlalchemy.orm import Session
from models.schemas import HealthAlert as SchemaHealthAlert
from database.models import HealthAlert as DBHealthAlert
from services.jira_service import JIRAService

# Set up logger
logger = logging.getLogger(__name__)

async def create_jira_ticket_for_alert(db: Session, alert_id: int) -> bool:
    """
    Creates a JIRA ticket for the specified alert and updates the alert
    with the ticket ID
    
    Args:
        db: Database session
        alert_id: ID of the alert to create a ticket for
        
    Returns:
        bool: True if the ticket was created successfully, False otherwise
    """
    try:
        # Get the alert
        db_alert = db.query(DBHealthAlert).filter(DBHealthAlert.id == alert_id).first()
        if not db_alert:
            logger.warning(f"Alert not found for JIRA ticket creation: ID {alert_id}")
            return False
        
        # Check if the alert already has a JIRA ticket
        if db_alert.jira_ticket_id:
            logger.info(f"Alert {alert_id} already has JIRA ticket: {db_alert.jira_ticket_id}")
            return True
        
        # Convert to schema for processing
        alert_schema = SchemaHealthAlert.model_validate(db_alert)
        
        # Create JIRA ticket
        jira_service = JIRAService()
        ticket_key = await jira_service.create_ticket(alert_schema)
        
        if not ticket_key:
            logger.error(f"Failed to create JIRA ticket for alert {alert_id}")
            return False
        
        # Update the alert with the ticket ID
        db_alert.jira_ticket_id = ticket_key
        db.commit()
        logger.info(f"Updated alert {alert_id} with JIRA ticket ID {ticket_key}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating JIRA ticket for alert {alert_id}: {str(e)}")
        db.rollback()
        return False