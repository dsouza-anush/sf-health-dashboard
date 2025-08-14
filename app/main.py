import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pathlib import Path

from database.db import get_db, engine
from database.models import Base
from database import seed
from app.api import router as api_router
from services import health_service

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Salesforce Health Check Dashboard")

# Set up templates directory
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Mount static files
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API router
app.include_router(api_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Render the dashboard home page."""
    stats = await health_service.get_dashboard_stats(db)
    alerts = await health_service.get_alerts(db, limit=10)
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "stats": stats, "alerts": alerts}
    )

@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request, db: Session = Depends(get_db)):
    """Render the alerts list page."""
    alerts = await health_service.get_alerts(db)
    return templates.TemplateResponse(
        "alerts.html",
        {"request": request, "alerts": alerts}
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
    
    return templates.TemplateResponse(
        "alert_detail.html",
        {"request": request, "alert": alert}
    )

@app.get("/categorize-all", response_class=HTMLResponse)
async def categorize_all_page(request: Request):
    """Render the categorize all alerts page."""
    return templates.TemplateResponse(
        "categorize_all.html",
        {"request": request}
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