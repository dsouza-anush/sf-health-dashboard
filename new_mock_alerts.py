import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.models import HealthAlert, HealthCategory, PriorityLevel, Base
from database.db import engine
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

def seed_additional_alerts():
    """Generate additional alerts with more variety for the dashboard."""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Additional varied alerts
    new_alerts = [
        # Alert with AI analysis but no categorization (in-progress state)
        HealthAlert(
            title="Just test",
            description="Test alert for verification purposes.",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "test", "purpose": "verification"}""",
            created_at=generate_timestamp(days_ago_max=1),
            ai_priority="low",
            ai_category="configuration"
        ),
        # Uncategorized alert (new alert)
        HealthAlert(
            title="Search performance degradation",
            description="Global search response times increased by 150% in the last 4 hours.",
            category="performance",
            source_system="Salesforce Monitoring",
            raw_data="""{"type": "performance", "component": "global-search", "avg_response_ms": 3200, "baseline_ms": 1250}""",
            created_at=generate_timestamp(days_ago_max=1)
        ),
        # High priority security alert
        HealthAlert(
            title="Unusual login patterns detected",
            description="User account 'admin@salesforce.com' logged in from 5 different countries in the past 24 hours.",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "suspicious_login", "user": "admin@salesforce.com", "countries": ["US", "RU", "CN", "BR", "NG"], "timeframe_hours": 24}""",
            created_at=generate_timestamp(days_ago_max=2),
            ai_category="security",
            ai_priority="high",
            ai_summary="Potential account compromise based on unusual login patterns",
            ai_recommendation="Lock the account immediately and contact the user through verified channels"
        ),
        # Critical API limit alert
        HealthAlert(
            title="Critical: API rate limit exceeded",
            description="External integration system has exceeded API rate limits 50 times in the past hour, causing service degradation.",
            category="limits",
            source_system="Salesforce Limits Health",
            raw_data="""{"type": "rate_limit", "service": "external-integration", "limit_type": "api_calls_per_hour", "exceeded_count": 50}""",
            created_at=generate_timestamp(days_ago_max=1),
            ai_category="code",
            ai_priority="critical",
            ai_summary="External system causing API throttling which impacts all integrations",
            ai_recommendation="Implement rate limiting on client side and optimize API usage patterns"
        ),
        # Medium priority performance issue
        HealthAlert(
            title="Batch job performance degradation",
            description="Nightly batch job execution time increased from 45 minutes to 2 hours.",
            category="performance",
            source_system="Salesforce Optimizer",
            raw_data="""{"type": "batch_job", "job_name": "AccountRecalculationBatch", "previous_duration_min": 45, "current_duration_min": 120}""",
            created_at=generate_timestamp(days_ago_max=3),
            ai_category="performance",
            ai_priority="medium",
            ai_summary="Batch job performance has declined significantly",
            ai_recommendation="Review database query patterns and add appropriate indexes"
        ),
        # Test alert for variety
        HealthAlert(
            title="test",
            description="Simple test alert for system verification",
            category="test",
            source_system="Salesforce Optimizer",
            raw_data="""{"type": "test", "purpose": "system verification"}""",
            created_at=generate_timestamp(days_ago_max=1),
            ai_category="configuration",
            ai_priority="medium"
        ),
        # More complex alerts with varied statuses
        HealthAlert(
            title="Object permission inconsistency",
            description="Profile 'Sales Representative' has View All Data permission on Contact but not on Account, creating data access issues.",
            category="security",
            source_system="Salesforce Security Health",
            raw_data="""{"type": "permission_audit", "profile": "Sales Representative", "object1": "Contact", "perm1": "ViewAllData", "object2": "Account", "perm2": "ViewAllData"}""",
            created_at=generate_timestamp(days_ago_max=5),
            ai_category="security",
            ai_priority="medium",
            ai_summary="Inconsistent object permissions causing data access issues",
            ai_recommendation="Standardize permissions across related objects or create permission sets"
        ),
        HealthAlert(
            title="High Apex CPU time usage",
            description="Trigger 'AccountAfterUpdate' consuming excessive CPU time and approaching governor limits.",
            category="performance",
            source_system="Salesforce Exceptions",
            raw_data="""{"type": "apex_cpu_time", "component": "AccountAfterUpdate", "avg_cpu_ms": 9800, "limit_ms": 10000, "percentage": 98}""",
            created_at=generate_timestamp(days_ago_max=2),
            ai_category="code",
            ai_priority="high",
            ai_summary="Trigger approaching CPU governor limits",
            ai_recommendation="Refactor trigger logic to be more efficient and use batch processing where appropriate"
        ),
        HealthAlert(
            title="Streaming API connection instability",
            description="PushTopic subscriptions experiencing frequent disconnections and reconnections.",
            category="stability",
            source_system="Salesforce Monitoring",
            raw_data="""{"type": "streaming_api", "disconnect_count": 47, "timeframe_hours": 3, "avg_uptime_min": 12}""",
            created_at=generate_timestamp(days_ago_max=3),
            ai_category="integration",
            ai_priority="medium",
            ai_summary="Frequent disconnections in streaming API affecting real-time data flow",
            ai_recommendation="Implement robust client-side reconnection logic and monitor network stability"
        ),
        HealthAlert(
            title="Report timeout frequency increasing",
            description="Dashboard reports timing out 32% more frequently than previous week.",
            category="performance",
            source_system="Salesforce Optimizer",
            raw_data="""{"type": "report_performance", "timeout_increase": 32, "most_affected": "Executive Dashboard", "avg_timeout_seconds": 65}""",
            created_at=generate_timestamp(days_ago_max=2),
            ai_category="performance",
            ai_priority="high",
            ai_summary="Reports timing out due to complex queries and large data volume",
            ai_recommendation="Optimize report filters, add indexed fields, and implement summary tables"
        ),
        # Various Resolved and Open alerts
        HealthAlert(
            title="Mobile app authentication failures",
            description="25% of mobile app users experiencing authentication failures when using biometric login.",
            category="security",
            source_system="Salesforce Mobile",
            raw_data="""{"type": "auth_failure", "platform": "mobile", "failure_rate": 25, "auth_method": "biometric", "affected_os": "iOS 15.x"}""",
            created_at=generate_timestamp(days_ago_max=6),
            is_resolved=True,
            updated_at=generate_timestamp(days_ago_max=2),
            ai_category="user experience",
            ai_priority="high",
            ai_summary="iOS biometric authentication failing due to API version mismatch",
            ai_recommendation="Update mobile authentication library to latest version"
        )
    ]
    
    db.add_all(new_alerts)
    db.commit()
    db.close()
    
    return len(new_alerts)

if __name__ == "__main__":
    count = seed_additional_alerts()
    print(f"Database seeded with {count} additional health alerts")