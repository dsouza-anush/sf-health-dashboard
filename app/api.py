from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.db import get_db
from models.schemas import HealthAlert, HealthAlertCreate, HealthAlertUpdate, AIInsights, InsightRequest
from services import health_service
from services.jira_integration import create_jira_ticket_for_alert
from services.heroku_insights_service import heroku_insights_service

router = APIRouter()

@router.get("/alerts/", response_model=List[HealthAlert])
async def read_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all health alerts with pagination."""
    alerts = await health_service.get_alerts(db, skip=skip, limit=limit)
    return alerts

@router.get("/alerts/{alert_id}", response_model=HealthAlert)
async def read_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific health alert by ID."""
    alert = await health_service.get_alert_by_id(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/alerts/", response_model=HealthAlert)
async def create_alert(alert: HealthAlertCreate, db: Session = Depends(get_db)):
    """Create a new health alert."""
    return await health_service.create_alert(db, alert)

@router.put("/alerts/{alert_id}", response_model=HealthAlert)
async def update_alert(alert_id: int, alert: HealthAlertUpdate, db: Session = Depends(get_db)):
    """Update an existing health alert."""
    updated_alert = await health_service.update_alert(db, alert_id, alert)
    if updated_alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return updated_alert

@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete a health alert."""
    success = await health_service.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted successfully"}

@router.get("/alerts/unresolved/", response_model=List[HealthAlert])
async def read_unresolved_alerts(db: Session = Depends(get_db)):
    """Get all unresolved health alerts."""
    return await health_service.get_unresolved_alerts(db)

@router.get("/alerts/uncategorized/", response_model=List[HealthAlert])
async def read_uncategorized_alerts(db: Session = Depends(get_db)):
    """Get all health alerts that haven't been categorized by AI yet."""
    return await health_service.get_uncategorized_alerts(db)

@router.post("/alerts/{alert_id}/categorize", response_model=HealthAlert)
async def categorize_alert(alert_id: int, db: Session = Depends(get_db)):
    """Categorize a specific health alert using AI."""
    alert = await health_service.categorize_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/alerts/{alert_id}/recategorize", response_model=HealthAlert)
async def recategorize_alert(alert_id: int, db: Session = Depends(get_db)):
    """Recategorize an already categorized health alert using AI."""
    # Same implementation as categorize_alert - the service function will override any existing categorization
    alert = await health_service.categorize_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/alerts/categorize-all")
async def categorize_all_alerts(db: Session = Depends(get_db)):
    """Categorize all uncategorized health alerts."""
    count = await health_service.categorize_all_uncategorized(db)
    return {"message": f"Categorized {count} alerts successfully"}

@router.put("/alerts/{alert_id}/resolve", response_model=HealthAlert)
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark a health alert as resolved."""
    alert = await health_service.mark_alert_resolved(db, alert_id, resolved=True)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.put("/alerts/{alert_id}/unresolve", response_model=HealthAlert)
async def unresolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark a health alert as unresolved."""
    alert = await health_service.mark_alert_resolved(db, alert_id, resolved=False)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get statistics for the dashboard."""
    return await health_service.get_dashboard_stats(db)

@router.get("/insights/", response_model=AIInsights)
async def get_ai_insights(time_range: str = "week"):
    """Get AI-generated insights on health alerts."""
    try:
        insights = await heroku_insights_service.get_ai_insights(time_range)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@router.post("/insights/", response_model=AIInsights)
async def request_ai_insights(request: InsightRequest):
    """Request AI-generated insights on health alerts with specific parameters."""
    try:
        insights = await heroku_insights_service.get_ai_insights(request.time_range.value)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@router.post("/alerts/create-and-categorize", response_model=HealthAlert)
async def create_and_categorize_alert(alert: HealthAlertCreate, db: Session = Depends(get_db)):
    """Create a new health alert and immediately categorize it with AI."""
    # First create the alert in the database
    new_alert = await health_service.create_alert(db, alert)
    
    # Then run AI categorization on it
    categorized_alert = await health_service.categorize_alert(db, new_alert.id)
    
    return categorized_alert
    
@router.post("/alerts/{alert_id}/create-jira")
async def create_jira_ticket(alert_id: int, db: Session = Depends(get_db)):
    """Create a JIRA ticket for a specific health alert."""
    # Get the alert first to check if it exists
    alert = await health_service.get_alert_by_id(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    # Check if the alert already has a JIRA ticket
    if alert.jira_ticket_id:
        return {"message": f"Alert already has JIRA ticket: {alert.jira_ticket_id}",
                "jira_ticket_id": alert.jira_ticket_id}
    
    # Create the JIRA ticket
    success = await create_jira_ticket_for_alert(db, alert_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create JIRA ticket")
    
    # Get the updated alert with the JIRA ticket ID
    updated_alert = await health_service.get_alert_by_id(db, alert_id)
    
    return {"message": f"Created JIRA ticket: {updated_alert.jira_ticket_id}", 
            "jira_ticket_id": updated_alert.jira_ticket_id}