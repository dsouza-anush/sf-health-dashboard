from sqlalchemy.orm import Session
from .models import HealthAlert, HealthCategory, PriorityLevel, Base
from .db import engine
import random
import datetime
from datetime import timezone, timedelta

def generate_timestamp(days_ago_max=30):
    """Generate a random timestamp within the last N days."""
    days_ago = random.randint(0, days_ago_max)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    seconds_ago = random.randint(0, 59)
    
    timestamp = datetime.datetime.now(timezone.utc) - timedelta(
        days=days_ago,
        hours=hours_ago,
        minutes=minutes_ago,
        seconds=seconds_ago
    )
    
    return timestamp

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
            raw_data="""{"type": "workflow_rules", "count": 32, "details": "List of inactive workflow rules", "last_execution": "2024-02-15"}""",
            created_at=generate_timestamp(days_ago_max=15)
        ),
        HealthAlert(
            title="Approaching field limit",
            description="Your org is using 85% of available custom fields. Consider field cleanup.",
            category="optimizer",
            source_system="Salesforce Optimizer",
            raw_data="""{"type": "field_usage", "current": 680, "limit": 800, "percentage": 85}""",
            created_at=generate_timestamp(days_ago_max=7)
        ),
        HealthAlert(
            title="Unused report types detected",
            description="15 custom report types have not been used in over 12 months. Consider cleanup to improve admin experience.",
            category="optimizer",
            source_system="Salesforce Optimizer",
            raw_data="""{"type": "report_types", "count": 15, "details": "List of unused report types", "last_usage": "2023-08-22"}""",
            created_at=generate_timestamp(days_ago_max=10),
            is_resolved=True,
            updated_at=generate_timestamp(days_ago_max=2)
        ),
        HealthAlert(
            title="Excessive profile duplication",
            description="Found 8 profiles with 90%+ permission similarity. Consider consolidating to reduce maintenance overhead.",
            category="optimizer",
            source_system="Salesforce Optimizer",
            raw_data="""{"type": "profile_duplication", "count": 8, "similarity_threshold": 90, "details": "Profile analysis results"}""",
            created_at=generate_timestamp(days_ago_max=20)
        ),
    ]
    
    # Salesforce Security Health
    security_alerts = [
        HealthAlert(
            title="Users with excessive permissions",
            description="15 users have Modify All Data permission but haven't used it in 90 days.",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "permission_audit", "permission": "ModifyAllData", "users_affected": 15, "risk_level": "high"}""",
            created_at=generate_timestamp(days_ago_max=3)
        ),
        HealthAlert(
            title="Password policy below recommended settings",
            description="Current password policy allows for passwords that are too simple (minimum 6 characters, no complexity requirements).",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "password_policy", "current_min_length": 6, "recommended_min_length": 8, "complexity_required": false}""",
            created_at=generate_timestamp(days_ago_max=14)
        ),
        HealthAlert(
            title="API user credential expiration",
            description="Integration user 'api-connector' credentials will expire in 7 days. Immediate rotation required.",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "credential_expiration", "user": "api-connector", "days_remaining": 7, "last_rotated": "2024-02-15"}""",
            created_at=generate_timestamp(days_ago_max=1)
        ),
        HealthAlert(
            title="Publicly accessible Apex classes",
            description="3 Apex classes are publicly accessible without proper authentication checks.",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "public_apex", "count": 3, "classes": ["DataExportController", "PublicFormHandler", "LegacyAPIEndpoint"], "risk_level": "high"}""",
            created_at=generate_timestamp(days_ago_max=5)
        ),
    ]
    
    # Salesforce Limits Health
    limits_alerts = [
        HealthAlert(
            title="API call limit approaching threshold",
            description="Current API usage at 83% of daily limit. Trending to exceed limit in the next 3 hours.",
            category="limits",
            source_system="Salesforce Limits Health",
            raw_data="""{"type": "api_usage", "current": 83000, "limit": 100000, "percentage": 83, "trend": "increasing"}""",
            created_at=generate_timestamp(days_ago_max=1)
        ),
        HealthAlert(
            title="Data storage nearing capacity",
            description="Organization is using 78% of available data storage. Consider archiving old data.",
            category="limits",
            source_system="Salesforce Limits Health",
            raw_data="""{"type": "storage", "current_gb": 780, "limit_gb": 1000, "percentage": 78}""",
            created_at=generate_timestamp(days_ago_max=5)
        ),
        HealthAlert(
            title="Governor limit exceptions increasing",
            description="SOQL query limit exceptions have increased by 35% in the past week. Most occurrences in ContactSyncBatch class.",
            category="limits",
            source_system="Salesforce Limits Health",
            raw_data="""{"type": "governor_limits", "exception_type": "SOQL_query_limit", "increase": 35, "period": "week", "source": "ContactSyncBatch"}""",
            created_at=generate_timestamp(days_ago_max=3)
        ),
        HealthAlert(
            title="Streaming API push topic quota at risk",
            description="87% of maximum streaming API push topics are in use. Only 13 more push topics can be created.",
            category="limits",
            source_system="Salesforce Limits Health",
            raw_data="""{"type": "push_topics", "current": 87, "limit": 100, "percentage": 87}""",
            created_at=generate_timestamp(days_ago_max=8),
            is_resolved=True,
            updated_at=generate_timestamp(days_ago_max=2)
        ),
    ]
    
    # Salesforce Event Health
    event_alerts = [
        HealthAlert(
            title="High rate of login failures",
            description="Detected abnormal spike in login failures from IP range 192.168.10.0/24 in the last hour.",
            category="event",
            source_system="Splunk Event Health",
            raw_data="""{"type": "login_failures", "count": 156, "timeframe": "last_hour", "ip_range": "192.168.10.0/24", "baseline": 15}""",
            created_at=generate_timestamp(days_ago_max=1)
        ),
        HealthAlert(
            title="Bulk API usage spike",
            description="Unusually high volume of Bulk API operations from integration user 'etl-service'.",
            category="event",
            source_system="Splunk Event Health",
            raw_data="""{"type": "bulk_api", "operations": 12500, "user": "etl-service", "timeframe": "last_30_minutes", "baseline": 5000}""",
            created_at=generate_timestamp(days_ago_max=2)
        ),
        HealthAlert(
            title="Scheduled job failure pattern",
            description="Weekly data export job has failed 3 consecutive times with timeout errors.",
            category="event",
            source_system="Splunk Event Health",
            raw_data="""{"type": "scheduled_job", "job_name": "Weekly_Data_Export", "consecutive_failures": 3, "error_type": "Timeout", "last_successful_run": "2024-07-24"}""",
            created_at=generate_timestamp(days_ago_max=4)
        ),
    ]
    
    # Application Stability Health
    stability_alerts = [
        HealthAlert(
            title="P1 Incident: Order Processing System Down",
            description="Critical failure in Order Processing system. Orders cannot be submitted or processed.",
            category="stability",
            source_system="ServiceNow",
            raw_data="""{"type": "incident", "priority": "P1", "incident_number": "INC0012345", "affected_system": "Order Processing", "start_time": "2024-08-14T08:23:15Z", "status": "In Progress"}""",
            created_at=generate_timestamp(days_ago_max=1)
        ),
        HealthAlert(
            title="P2 Incident: Slow Performance in Quote Generation",
            description="Users reporting 30+ second delays when generating quotes for customers.",
            category="stability",
            source_system="ServiceNow",
            raw_data="""{"type": "incident", "priority": "P2", "incident_number": "INC0012346", "affected_system": "Quote Generator", "start_time": "2024-08-13T15:45:22Z", "status": "Investigating"}""",
            created_at=generate_timestamp(days_ago_max=3)
        ),
        HealthAlert(
            title="P3 Incident: Customer Search Returning Incomplete Results",
            description="Global search function not returning all relevant customer records.",
            category="stability",
            source_system="ServiceNow",
            raw_data="""{"type": "incident", "priority": "P3", "incident_number": "INC0012347", "affected_system": "Global Search", "start_time": "2024-08-12T09:12:45Z", "status": "Under Investigation"}""",
            created_at=generate_timestamp(days_ago_max=5),
            is_resolved=True,
            updated_at=generate_timestamp(days_ago_max=1)
        ),
    ]
    
    # Salesforce Portal Health
    portal_alerts = [
        HealthAlert(
            title="High error rate on Customer Portal login page",
            description="15% of Customer Portal login attempts resulting in error in the past 2 hours.",
            category="portal",
            source_system="Salesforce Portal Health",
            raw_data="""{"type": "error_rate", "page": "login", "rate": 15, "timeframe": "2_hours", "threshold": 5}""",
            created_at=generate_timestamp(days_ago_max=1)
        ),
        HealthAlert(
            title="Partner Portal page load times exceeding threshold",
            description="Average page load time for Partner Portal catalog pages: 5.2 seconds (threshold: 3 seconds).",
            category="portal",
            source_system="Salesforce Portal Health",
            raw_data="""{"type": "page_load", "page": "partner_catalog", "avg_time_seconds": 5.2, "threshold": 3}""",
            created_at=generate_timestamp(days_ago_max=4)
        ),
        HealthAlert(
            title="Customer Portal file download failures",
            description="25% of document downloads in Customer Portal failing with access errors.",
            category="portal",
            source_system="Salesforce Portal Health",
            raw_data="""{"type": "download_errors", "error_rate": 25, "error_type": "Access Denied", "affected_component": "Document Library"}""",
            created_at=generate_timestamp(days_ago_max=2)
        ),
    ]
    
    # Salesforce Exceptions Health
    exceptions_alerts = [
        HealthAlert(
            title="High volume of SOQL limit exceptions",
            description="Integration user 'data-sync' generating frequent SOQL query limit exceptions during sync operations.",
            category="exceptions",
            source_system="Salesforce Exceptions",
            raw_data="""{"type": "apex_exception", "exception_type": "System.LimitException", "message": "Too many SOQL queries: 101", "context": "DataSyncBatch", "count": 28, "user": "data-sync"}""",
            created_at=generate_timestamp(days_ago_max=2)
        ),
        HealthAlert(
            title="Callout exceptions to external payment service",
            description="Multiple callout exceptions when connecting to payment gateway API in the last 4 hours.",
            category="exceptions",
            source_system="Salesforce Exceptions",
            raw_data="""{"type": "apex_exception", "exception_type": "System.CalloutException", "message": "Read timed out", "context": "PaymentProcessor", "count": 12, "external_service": "payment-gateway-api"}""",
            created_at=generate_timestamp(days_ago_max=1)
        ),
        HealthAlert(
            title="Recurring DML exceptions in batch process",
            description="Weekly account update batch failing with DML exceptions affecting 230 records.",
            category="exceptions",
            source_system="Salesforce Exceptions",
            raw_data="""{"type": "apex_exception", "exception_type": "System.DmlException", "message": "UNABLE_TO_LOCK_ROW", "context": "AccountUpdateBatch", "count": 15, "records_affected": 230}""",
            created_at=generate_timestamp(days_ago_max=7),
            is_resolved=True,
            updated_at=generate_timestamp(days_ago_max=3)
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
    
    # Add AI analysis to alerts for demo purposes
    
    # Optimizer alerts
    all_alerts[0].ai_category = "Configuration"
    all_alerts[0].ai_priority = "medium"
    all_alerts[0].ai_summary = "Large number of unused workflow rules creating technical debt"
    all_alerts[0].ai_recommendation = "Review and clean up inactive workflow rules to improve system maintainability"
    
    all_alerts[1].ai_category = "Maintenance"
    all_alerts[1].ai_priority = "high"
    all_alerts[1].ai_summary = "Approaching field limit could prevent future customizations"
    all_alerts[1].ai_recommendation = "Audit and remove unused custom fields; consider consolidation of similar fields"
    
    all_alerts[2].ai_category = "Configuration"
    all_alerts[2].ai_priority = "low"
    all_alerts[2].ai_summary = "Unused report types adding unnecessary complexity to reporting system"
    all_alerts[2].ai_recommendation = "Clean up unused report types to improve admin experience"
    
    # Security alerts
    all_alerts[4].ai_category = "Security"
    all_alerts[4].ai_priority = "high"
    all_alerts[4].ai_summary = "Over-provisioned user permissions creating security vulnerability"
    all_alerts[4].ai_recommendation = "Implement least privilege access by removing unused permissions"
    
    all_alerts[5].ai_category = "Security"
    all_alerts[5].ai_priority = "medium"
    all_alerts[5].ai_summary = "Weak password policy increases risk of unauthorized access"
    all_alerts[5].ai_recommendation = "Update password policy to require minimum 12 characters with complexity requirements"
    
    all_alerts[6].ai_category = "Security"
    all_alerts[6].ai_priority = "critical"
    all_alerts[6].ai_summary = "Expiring API credentials could cause service disruption"
    all_alerts[6].ai_recommendation = "Immediately rotate API credentials and update all connected systems"
    
    # Limits alerts
    all_alerts[8].ai_category = "Performance"
    all_alerts[8].ai_priority = "critical"
    all_alerts[8].ai_summary = "API usage approaching limit which may cause service interruption"
    all_alerts[8].ai_recommendation = "Optimize API calls or request limit increase before threshold is reached"
    
    all_alerts[9].ai_category = "Infrastructure"
    all_alerts[9].ai_priority = "high"
    all_alerts[9].ai_summary = "Storage capacity constraints could impact system operations"
    all_alerts[9].ai_recommendation = "Implement data archiving strategy for records older than 2 years"
    
    # Event alerts
    all_alerts[12].ai_category = "Security"
    all_alerts[12].ai_priority = "critical"
    all_alerts[12].ai_summary = "Potential brute force attack detected from specific IP range"
    all_alerts[12].ai_recommendation = "Block IP range immediately and investigate affected user accounts"
    
    # Stability alerts
    all_alerts[15].ai_category = "Availability"
    all_alerts[15].ai_priority = "critical"
    all_alerts[15].ai_summary = "Critical business process unavailable affecting all users"
    all_alerts[15].ai_recommendation = "Implement emergency recovery protocol and notify executive stakeholders"
    
    # Portal alerts
    all_alerts[18].ai_category = "User Experience"
    all_alerts[18].ai_priority = "high"
    all_alerts[18].ai_summary = "Customer portal errors causing negative user experience"
    all_alerts[18].ai_recommendation = "Investigate auth provider integration and implement client-side error handling"
    
    # Exceptions alerts
    all_alerts[21].ai_category = "Code Quality"
    all_alerts[21].ai_priority = "high"
    all_alerts[21].ai_summary = "Inefficient SOQL queries causing governor limit exceptions"
    all_alerts[21].ai_recommendation = "Refactor DataSyncBatch class to use bulk queries and reduce query count"
    
    db.add_all(all_alerts)
    db.commit()
    db.close()
    
    return len(all_alerts)

if __name__ == "__main__":
    count = seed_database()
    print(f"Database seeded with {count} health alerts")