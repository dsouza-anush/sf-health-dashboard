import asyncio
import os
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Add project root to Python path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import HealthAlert, Base
from database.seed import seed_database
from services.health_service import get_alerts, get_dashboard_stats, categorize_alert
from models.schemas import HealthAlert as SchemaHealthAlert

async def test_database_connection():
    print("Testing database connection...")
    try:
        # Connect to database using DATABASE_URL from .env
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            print("ERROR: No DATABASE_URL found in environment")
            return False
        
        engine = create_engine(DATABASE_URL)
        try:
            # Try to connect
            connection = engine.connect()
            connection.close()
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return False
    except Exception as e:
        print(f"❌ Error in test_database_connection: {str(e)}")
        return False

async def test_database_seed():
    print("\nTesting database seeding...")
    try:
        count = seed_database()
        print(f"✅ Seeded database with {count} alerts")
        return True
    except Exception as e:
        print(f"❌ Database seeding failed: {str(e)}")
        return False

async def test_get_alerts():
    print("\nTesting alert retrieval...")
    try:
        # Create a database session
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get alerts
        alerts = await get_alerts(db)
        print(f"✅ Retrieved {len(alerts)} alerts")
        
        # Show a sample alert
        if alerts:
            sample = alerts[0]
            print(f"Sample alert: {sample.title} ({sample.category})")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Alert retrieval failed: {str(e)}")
        return False

async def test_dashboard_stats():
    print("\nTesting dashboard statistics...")
    try:
        # Create a database session
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get stats
        stats = await get_dashboard_stats(db)
        print(f"✅ Retrieved dashboard stats")
        print(f"Total alerts: {stats['total_alerts']}")
        print(f"Unresolved alerts: {stats['unresolved_alerts']}")
        print(f"Alerts by category: {stats['by_category']}")
        print(f"Alerts by priority: {stats['by_priority']}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Dashboard stats retrieval failed: {str(e)}")
        return False

async def test_ai_categorization():
    print("\nTesting AI categorization...")
    try:
        # Check if AI API key exists
        load_dotenv()
        api_key = os.getenv("INFERENCE_API_KEY") or os.getenv("INFERENCE_KEY") or os.getenv("HEROKU_INFERENCE_API_KEY")
        if not api_key:
            print("⚠️ No AI API key found in environment - skipping actual categorization")
            print("ℹ️ The system will still function with default categorizations")
            return True
        
        # Create a database session
        DATABASE_URL = os.getenv("DATABASE_URL")
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get alerts and try to categorize one
        alerts = await get_alerts(db)
        if alerts:
            uncategorized = next((alert for alert in alerts if not alert.ai_category), None)
            if uncategorized:
                alert_id = uncategorized.id
                print(f"Testing categorization on alert ID {alert_id}...")
                result = await categorize_alert(db, alert_id)
                if result and result.ai_category:
                    print(f"✅ Successfully categorized alert: {result.ai_category} (priority: {result.ai_priority})")
                    print(f"Summary: {result.ai_summary}")
                    print(f"Recommendation: {result.ai_recommendation}")
                else:
                    print("⚠️ Categorization completed but no category was assigned")
            else:
                print("ℹ️ All alerts already categorized - skipping test")
        else:
            print("ℹ️ No alerts found for categorization test")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ AI categorization test failed: {str(e)}")
        return False

async def run_all_tests():
    print("=== Running tests for Salesforce Health Dashboard ===\n")
    
    db_connection = await test_database_connection()
    if not db_connection:
        print("\n❌ Database connection failed - cannot proceed with other tests")
        return
    
    await test_database_seed()
    await test_get_alerts()
    await test_dashboard_stats()
    await test_ai_categorization()
    
    print("\n=== Tests complete ===")

if __name__ == "__main__":
    asyncio.run(run_all_tests())