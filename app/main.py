import os
import time
import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

from database.db import get_db, engine
from database.models import Base
from database import seed
from app.api import router as api_router
from app.slack_events import router as slack_router
from services import health_service

# Load environment variables
load_dotenv()

# Create database tables with retry for Heroku startup
max_retries = 5
for attempt in range(max_retries):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database tables created successfully on attempt {attempt + 1}")
        break
    except OperationalError as e:
        if attempt < max_retries - 1:
            logger.warning(f"Database connection failed on attempt {attempt + 1}: {str(e)}")
            logger.info("Retrying in 3 seconds...")
            time.sleep(3)
        else:
            logger.error(f"Failed to create database tables after {max_retries} attempts: {str(e)}")
            # Continue anyway - tables might exist already

# Initialize FastAPI app
app = FastAPI(title="Salesforce Health Check Dashboard")

# Set up templates directory
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Mount static files
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Include Slack events router
app.include_router(slack_router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Render the dashboard home page."""
    try:
        # Get dashboard stats and alerts
        stats = await health_service.get_dashboard_stats(db)
        alerts = await health_service.get_alerts(db, limit=10)
        
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "stats": stats, "alerts": alerts}
        )
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "An error occurred while loading the dashboard. Please try again later."}
        )

@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request, db: Session = Depends(get_db)):
    """Render the alerts list page."""
    try:
        # Get all alerts from database
        alerts = await health_service.get_alerts(db)
            
        return templates.TemplateResponse(
            "alerts.html",
            {"request": request, "alerts": alerts}
        )
    except Exception as e:
        logger.error(f"Error rendering alerts page: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "An error occurred while loading alerts. Please try again later."}
        )

@app.get("/alert/{alert_id}", response_class=HTMLResponse)
async def alert_detail(request: Request, alert_id: int, db: Session = Depends(get_db)):
    """Render the alert detail page."""
    alert = await health_service.get_alert_by_id(db, alert_id)
    if not alert:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Alert not found"}
        )
    
    # Get JIRA domain from environment for link generation
    jira_domain = os.getenv("JIRA_DOMAIN", "")
    
    return templates.TemplateResponse(
        "alert_detail.html",
        {"request": request, "alert": alert, "jira_domain": jira_domain}
    )

@app.get("/categorize-all", response_class=HTMLResponse)
async def categorize_all_page(request: Request):
    """Render the categorize all alerts page."""
    return templates.TemplateResponse(
        "categorize_all.html",
        {"request": request}
    )

@app.get("/create-ticket", response_class=HTMLResponse)
async def create_ticket_page(request: Request):
    """Render the create ticket page with AI categorization demo."""
    try:
        return templates.TemplateResponse(
            "create_ticket_modern.html",
            {"request": request}
        )
    except Exception as e:
        logger.error(f"Error rendering create_ticket page: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "An error occurred while loading the create ticket page. Please try again later."}
        )

@app.get("/seed-database")
async def seed_db():
    """Seed the database with sample data."""
    count = seed.seed_database()
    return {"message": f"Database seeded with {count} sample alerts"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)