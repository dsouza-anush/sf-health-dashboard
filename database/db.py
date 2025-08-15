import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

# Set up logger
logger = logging.getLogger(__name__)

load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sf_health")

# Handle special case for Heroku Postgres
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Log database connection (with credentials hidden)
db_url_parts = DATABASE_URL.split('@')
if len(db_url_parts) > 1:
    logger.info(f"Connecting to database at: {db_url_parts[0].split('://')[0]}://*****@{db_url_parts[1]}")
else:
    logger.info(f"Connecting to database at: {DATABASE_URL}")

# Configure engine with optimized settings for Heroku
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # Reasonable pool size for web applications
    max_overflow=10,  # Allow up to 10 additional connections when pool is fully used
    pool_timeout=30,  # Seconds to wait for a connection from pool
    pool_recycle=1800,  # Recycle connections every 30 minutes to avoid stale connections
    connect_args={"connect_timeout": 10}  # Timeout after 10 seconds if connection can't be established
)

# Set up ping listener to check connections before using them
@event.listens_for(Engine, "engine_connect")
def ping_connection(connection, branch):
    if branch:
        # Don't ping on sub-connections (e.g., inside transactions)
        return

    # Perform a simple query to verify connection is still valid
    try:
        connection.scalar(text("SELECT 1"))
    except Exception as e:
        # Recycle the connection if there's an issue
        logger.warning(f"Connection ping failed, recycling connection: {str(e)}")
        connection.invalidate()
        raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

def get_db():
    """Dependency for FastAPI routes that need a database session.
    
    This function creates a new database session for each request and ensures
    that the session is properly closed when the request is complete, even if
    an exception occurs.
    
    Yields:
        SQLAlchemy Session: A database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()  # Rollback any pending transactions on error
        raise  # Re-raise the exception for FastAPI to handle
    finally:
        db.close()  # Always close the session