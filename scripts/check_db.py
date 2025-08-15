#!/usr/bin/env python3
import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import engine, get_db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if the database connection is working and tables exist"""
    try:
        with engine.connect() as conn:
            # Try to execute a simple query
            result = conn.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                logger.info("Database connection successful!")
            
            # Check if health_alerts table exists
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM health_alerts"))
                count = result.fetchone()[0]
                logger.info(f"Found {count} records in health_alerts table")
            except Exception as e:
                logger.error(f"Error checking health_alerts table: {str(e)}")
                logger.info("The table might not exist. You may need to run migrations or seed data.")
    
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False
    
    return True

def check_environment_variables():
    """Check environment variables related to databases"""
    logger.info("Checking database environment variables...")
    
    db_url = os.getenv("DATABASE_URL")
    logger.info(f"DATABASE_URL is {'set' if db_url else 'not set'}")
    
    cobalt_url = os.getenv("HEROKU_POSTGRESQL_COBALT_URL")
    logger.info(f"HEROKU_POSTGRESQL_COBALT_URL is {'set' if cobalt_url else 'not set'}")
    
    amber_url = os.getenv("HEROKU_POSTGRESQL_AMBER_URL")
    logger.info(f"HEROKU_POSTGRESQL_AMBER_URL is {'set' if amber_url else 'not set'}")
    
    # Check if URLs are the same
    if db_url and cobalt_url:
        logger.info(f"DATABASE_URL and COBALT URL are {'the same' if db_url == cobalt_url else 'different'}")
    if db_url and amber_url:
        logger.info(f"DATABASE_URL and AMBER URL are {'the same' if db_url == amber_url else 'different'}")

if __name__ == "__main__":
    logger.info("Starting database check...")
    check_environment_variables()
    check_database_connection()