import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database.models import HealthAlert as DBHealthAlert, HealthCategory
from models.schemas import HealthAlertCreate, HealthAlertUpdate, HealthAlert as SchemaHealthAlert
from services.ai_service import categorize_health_alert

# Set up logger
logger = logging.getLogger(__name__)

async def get_alerts(db: Session, skip: int = 0, limit: int = 100) -> List[SchemaHealthAlert]:
    """Get a list of health alerts from the database."""
    alerts = db.query(DBHealthAlert).offset(skip).limit(limit).all()
    return [SchemaHealthAlert.model_validate(alert) for alert in alerts]

async def get_alert_by_id(db: Session, alert_id: int) -> Optional[SchemaHealthAlert]:
    """Get a specific health alert by ID."""
    alert = db.query(DBHealthAlert).filter(DBHealthAlert.id == alert_id).first()
    if alert:
        return SchemaHealthAlert.model_validate(alert)
    return None

async def create_alert(db: Session, alert_data: HealthAlertCreate) -> SchemaHealthAlert:
    """Create a new health alert."""
    db_alert = DBHealthAlert(**alert_data.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return SchemaHealthAlert.model_validate(db_alert)

async def update_alert(db: Session, alert_id: int, alert_data: HealthAlertUpdate) -> Optional[SchemaHealthAlert]:
    """Update an existing health alert."""
    db_alert = db.query(DBHealthAlert).filter(DBHealthAlert.id == alert_id).first()
    if not db_alert:
        return None
    
    update_data = alert_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_alert, key, value)
    
    db.commit()
    db.refresh(db_alert)
    return SchemaHealthAlert.model_validate(db_alert)

async def delete_alert(db: Session, alert_id: int) -> bool:
    """Delete a health alert."""
    db_alert = db.query(DBHealthAlert).filter(DBHealthAlert.id == alert_id).first()
    if not db_alert:
        return False
    
    db.delete(db_alert)
    db.commit()
    return True

async def get_alerts_by_category(db: Session, category: str) -> List[SchemaHealthAlert]:
    """Get health alerts by category."""
    alerts = db.query(DBHealthAlert).filter(DBHealthAlert.category == category).all()
    return [SchemaHealthAlert.model_validate(alert) for alert in alerts]

async def get_unresolved_alerts(db: Session) -> List[SchemaHealthAlert]:
    """Get all unresolved health alerts."""
    alerts = db.query(DBHealthAlert).filter(DBHealthAlert.is_resolved == False).all()
    return [SchemaHealthAlert.model_validate(alert) for alert in alerts]

async def get_uncategorized_alerts(db: Session) -> List[SchemaHealthAlert]:
    """Get all health alerts that haven't been categorized by AI yet."""
    alerts = db.query(DBHealthAlert).filter(DBHealthAlert.ai_category.is_(None)).all()
    return [SchemaHealthAlert.model_validate(alert) for alert in alerts]

async def mark_alert_resolved(db: Session, alert_id: int, resolved: bool = True) -> Optional[SchemaHealthAlert]:
    """Mark a health alert as resolved or unresolved."""
    db_alert = db.query(DBHealthAlert).filter(DBHealthAlert.id == alert_id).first()
    if not db_alert:
        return None
    
    db_alert.is_resolved = resolved
    db.commit()
    db.refresh(db_alert)
    return SchemaHealthAlert.model_validate(db_alert)

async def categorize_alert(db: Session, alert_id: int) -> Optional[SchemaHealthAlert]:
    """Categorize a health alert using the AI service."""
    try:
        # Get the alert by ID
        db_alert = db.query(DBHealthAlert).filter(DBHealthAlert.id == alert_id).first()
        if not db_alert:
            logger.warning(f"Alert not found for categorization: ID {alert_id}")
            return None
        
        logger.info(f"Categorizing alert {alert_id}: {db_alert.title}")
        
        # Convert to schema for AI processing
        alert_schema = SchemaHealthAlert.model_validate(db_alert)
        
        # Get AI categorization
        ai_result = await categorize_health_alert(alert_schema)
        
        # Clean up and normalize results
        category = ai_result.category.strip().lower()
        
        # Map to one of our standard categories if needed
        standard_categories = ["configuration", "security", "performance", "data", 
                            "integration", "compliance", "code", "user experience"]
        
        # Find the closest matching category if needed
        if category not in standard_categories:
            logger.debug(f"Non-standard category received: {category}, finding closest match")
            for std_cat in standard_categories:
                if std_cat in category:
                    category = std_cat
                    logger.debug(f"Mapped to standard category: {category}")
                    break
            else:
                # Default to configuration if no match found
                logger.debug(f"No match found, using default category 'configuration'")
                category = "configuration" 
        
        # Update the database record with AI results
        db_alert.ai_category = category
        db_alert.ai_priority = ai_result.priority
        db_alert.ai_summary = ai_result.summary
        db_alert.ai_recommendation = ai_result.recommendation
        db_alert.updated_at = datetime.utcnow()  # Update timestamp
        
        db.commit()
        db.refresh(db_alert)
        
        logger.info(f"Alert {alert_id} categorized as {category} with {ai_result.priority} priority")
        return SchemaHealthAlert.model_validate(db_alert)
    except Exception as e:
        logger.error(f"Error categorizing alert {alert_id}: {str(e)}")
        db.rollback()  # Roll back transaction on error
        raise  # Re-raise to be handled at API level

async def categorize_all_uncategorized(db: Session) -> int:
    """Categorize all health alerts that haven't been categorized yet."""
    try:
        # Get all uncategorized alerts
        uncategorized = db.query(DBHealthAlert).filter(DBHealthAlert.ai_category.is_(None)).all()
        logger.info(f"Found {len(uncategorized)} uncategorized alerts")
        
        count = 0
        errors = 0
        
        # Process each alert individually
        for alert in uncategorized:
            alert_schema = SchemaHealthAlert.model_validate(alert)
            try:
                # Get AI categorization for this alert
                ai_result = await categorize_health_alert(alert_schema)
                
                # Update the database record with AI results
                alert.ai_category = ai_result.category
                alert.ai_priority = ai_result.priority
                alert.ai_summary = ai_result.summary
                alert.ai_recommendation = ai_result.recommendation
                alert.updated_at = datetime.utcnow()  # Update timestamp
                count += 1
                
                # Commit each update individually to avoid losing all work if one fails
                db.commit()
                logger.info(f"Categorized alert {alert.id}: {alert.title}")
                
            except Exception as e:
                # Log error but continue processing other alerts
                logger.error(f"Error categorizing alert {alert.id}: {str(e)}")
                db.rollback()  # Roll back failed transaction
                errors += 1
        
        logger.info(f"Categorization complete: {count} alerts processed successfully, {errors} errors")
        return count
        
    except Exception as e:
        logger.error(f"Error in batch categorization: {str(e)}")
        db.rollback()
        return 0  # Return 0 to indicate no alerts were categorized

async def get_dashboard_stats(db: Session) -> dict:
    """Get statistics for the dashboard."""
    total_alerts = db.query(DBHealthAlert).count()
    unresolved_alerts = db.query(DBHealthAlert).filter(DBHealthAlert.is_resolved == False).count()
    
    # Count by priority
    priorities = {
        "critical": db.query(DBHealthAlert).filter(DBHealthAlert.ai_priority == "critical").count(),
        "high": db.query(DBHealthAlert).filter(DBHealthAlert.ai_priority == "high").count(),
        "medium": db.query(DBHealthAlert).filter(DBHealthAlert.ai_priority == "medium").count(),
        "low": db.query(DBHealthAlert).filter(DBHealthAlert.ai_priority == "low").count(),
        "uncategorized": db.query(DBHealthAlert).filter(DBHealthAlert.ai_priority.is_(None)).count()
    }
    
    # Count by category
    categories = {}
    for category in ["optimizer", "security", "limits", "event", "stability", "portal", "exceptions"]:
        categories[category] = db.query(DBHealthAlert).filter(DBHealthAlert.category == category).count()
    
    # Count by AI category
    ai_categories = {}
    ai_category_results = db.query(DBHealthAlert.ai_category, func.count(DBHealthAlert.id)) \
        .filter(DBHealthAlert.ai_category.isnot(None)) \
        .group_by(DBHealthAlert.ai_category) \
        .all()
    
    for category, count in ai_category_results:
        ai_categories[category] = count
    
    return {
        "total_alerts": total_alerts,
        "unresolved_alerts": unresolved_alerts,
        "by_priority": priorities,
        "by_category": categories,
        "by_ai_category": ai_categories
    }