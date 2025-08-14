import sys
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: No DATABASE_URL found in environment")
    sys.exit(1)

# Handle special case for Heroku Postgres
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
engine = create_engine(DATABASE_URL)

def run_migrations():
    print("Running migrations...")
    
    with engine.begin() as conn:
        # Check if tables exist
        result = conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'health_alerts')"
        ))
        table_exists = result.scalar()
        
        if table_exists:
            print("Dropping existing tables...")
            conn.execute(text("DROP TABLE IF EXISTS health_alerts CASCADE"))
        
        # Create tables with proper types
        print("Creating tables...")
        conn.execute(text("""
        CREATE TABLE health_alerts (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(50) NOT NULL,
            source_system VARCHAR(100) NOT NULL,
            raw_data TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            ai_category VARCHAR(100),
            ai_priority VARCHAR(50),
            ai_summary TEXT,
            ai_recommendation TEXT,
            is_resolved BOOLEAN DEFAULT FALSE,
            jira_ticket_id VARCHAR(50),
            slack_alert_sent BOOLEAN DEFAULT FALSE
        )
        """))
        
        print("Migration complete!")
        return True

if __name__ == "__main__":
    run_migrations()