from sqlalchemy.orm import Session
from .models import HealthAlert, HealthCategory, PriorityLevel, Base
from .db import engine

def seed_database():
    """Seed the database with mock data for each health category."""
    Base.metadata.create_all(bind=engine)
    
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Delete existing records
    db.query(HealthAlert).delete()
    db.commit()
    
    # Salesforce Optimizer Health
    optimizer_alerts = [
        HealthAlert(
            title="High number of inactive workflow rules",
            description="There are 32 workflow rules that have not been activated in the past 6 months.",
            category="optimizer",
            source_system="Salesforce Optimizer",
            raw_data="""{"type": "workflow_rules", "count": 32, "details": "List of inactive workflow rules", "last_execution": "2024-02-15"}"""
        ),
        HealthAlert(
            title="Approaching field limit",
            description="Your org is using 85% of available custom fields. Consider field cleanup.",
            category="optimizer",
            source_system="Salesforce Optimizer",
            raw_data="""{"type": "field_usage", "current": 680, "limit": 800, "percentage": 85}"""
        ),
    ]
    
    # Salesforce Security Health
    security_alerts = [
        HealthAlert(
            title="Users with excessive permissions",
            description="15 users have Modify All Data permission but haven't used it in 90 days.",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "permission_audit", "permission": "ModifyAllData", "users_affected": 15, "risk_level": "high"}"""
        ),
        HealthAlert(
            title="Password policy below recommended settings",
            description="Current password policy allows for passwords that are too simple (minimum 6 characters, no complexity requirements).",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "password_policy", "current_min_length": 6, "recommended_min_length": 8, "complexity_required": false}"""
        ),
    ]
    
    # Salesforce Limits Health
    limits_alerts = [
        HealthAlert(
            title="API call limit approaching threshold",
            description="Current API usage at 83% of daily limit. Trending to exceed limit in the next 3 hours.",
            category="limits",
            source_system="Salesforce Limits Health",
            raw_data="""{"type": "api_usage", "current": 83000, "limit": 100000, "percentage": 83, "trend": "increasing"}"""
        ),
        HealthAlert(
            title="Data storage nearing capacity",
            description="Organization is using 78% of available data storage. Consider archiving old data.",
            category="limits",
            source_system="Salesforce Limits Health",
            raw_data="""{"type": "storage", "current_gb": 780, "limit_gb": 1000, "percentage": 78}"""
        ),
    ]
    
    # Salesforce Event Health
    event_alerts = [
        HealthAlert(
            title="High rate of login failures",
            description="Detected abnormal spike in login failures from IP range 192.168.10.0/24 in the last hour.",
            category="event",
            source_system="Splunk Event Health",
            raw_data="""{"type": "login_failures", "count": 156, "timeframe": "last_hour", "ip_range": "192.168.10.0/24", "baseline": 15}"""
        ),
        HealthAlert(
            title="Bulk API usage spike",
            description="Unusually high volume of Bulk API operations from integration user 'etl-service'.",
            category="event",
            source_system="Splunk Event Health",
            raw_data="""{"type": "bulk_api", "operations": 12500, "user": "etl-service", "timeframe": "last_30_minutes", "baseline": 5000}"""
        ),
    ]
    
    # Application Stability Health
    stability_alerts = [
        HealthAlert(
            title="P1 Incident: Order Processing System Down",
            description="Critical failure in Order Processing system. Orders cannot be submitted or processed.",
            category="stability",
            source_system="ServiceNow",
            raw_data="""{"type": "incident", "priority": "P1", "incident_number": "INC0012345", "affected_system": "Order Processing", "start_time": "2024-08-14T08:23:15Z", "status": "In Progress"}"""
        ),
        HealthAlert(
            title="P2 Incident: Slow Performance in Quote Generation",
            description="Users reporting 30+ second delays when generating quotes for customers.",
            category="stability",
            source_system="ServiceNow",
            raw_data="""{"type": "incident", "priority": "P2", "incident_number": "INC0012346", "affected_system": "Quote Generator", "start_time": "2024-08-13T15:45:22Z", "status": "Investigating"}"""
        ),
    ]
    
    # Salesforce Portal Health
    portal_alerts = [
        HealthAlert(
            title="High error rate on Customer Portal login page",
            description="15% of Customer Portal login attempts resulting in error in the past 2 hours.",
            category="portal",
            source_system="Salesforce Portal Health",
            raw_data="""{"type": "error_rate", "page": "login", "rate": 15, "timeframe": "2_hours", "threshold": 5}"""
        ),
        HealthAlert(
            title="Partner Portal page load times exceeding threshold",
            description="Average page load time for Partner Portal catalog pages: 5.2 seconds (threshold: 3 seconds).",
            category="portal",
            source_system="Salesforce Portal Health",
            raw_data="""{"type": "page_load", "page": "partner_catalog", "avg_time_seconds": 5.2, "threshold": 3}"""
        ),
    ]
    
    # Salesforce Exceptions Health
    exceptions_alerts = [
        HealthAlert(
            title="High volume of SOQL limit exceptions",
            description="Integration user 'data-sync' generating frequent SOQL query limit exceptions during sync operations.",
            category="exceptions",
            source_system="Salesforce Exceptions",
            raw_data="""{"type": "apex_exception", "exception_type": "System.LimitException", "message": "Too many SOQL queries: 101", "context": "DataSyncBatch", "count": 28, "user": "data-sync"}"""
        ),
        HealthAlert(
            title="Callout exceptions to external payment service",
            description="Multiple callout exceptions when connecting to payment gateway API in the last 4 hours.",
            category="exceptions",
            source_system="Salesforce Exceptions",
            raw_data="""{"type": "apex_exception", "exception_type": "System.CalloutException", "message": "Read timed out", "context": "PaymentProcessor", "count": 12, "external_service": "payment-gateway-api"}"""
        ),
    ]
    
    all_alerts = (
        optimizer_alerts + 
        security_alerts + 
        limits_alerts + 
        event_alerts + 
        stability_alerts + 
        portal_alerts +
        exceptions_alerts
    )
    
    # Add AI analysis to some alerts for demo purposes
    all_alerts[0].ai_category = "Configuration"
    all_alerts[0].ai_priority = "medium"
    all_alerts[0].ai_summary = "Large number of unused workflow rules creating technical debt"
    all_alerts[0].ai_recommendation = "Review and clean up inactive workflow rules to improve system maintainability"
    
    all_alerts[2].ai_category = "Security"
    all_alerts[2].ai_priority = "high"
    all_alerts[2].ai_summary = "Over-provisioned user permissions creating security vulnerability"
    all_alerts[2].ai_recommendation = "Implement least privilege access by removing unused permissions"
    
    all_alerts[4].ai_category = "Performance"
    all_alerts[4].ai_priority = "critical"
    all_alerts[4].ai_summary = "API usage approaching limit which may cause service interruption"
    all_alerts[4].ai_recommendation = "Optimize API calls or request limit increase before threshold is reached"
    
    db.add_all(all_alerts)
    db.commit()
    db.close()
    
    return len(all_alerts)

if __name__ == "__main__":
    count = seed_database()
    print(f"Database seeded with {count} health alerts")