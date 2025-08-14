from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class PriorityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class HealthCategory(str, enum.Enum):
    OPTIMIZER = "optimizer"
    SECURITY = "security"
    LIMITS = "limits"
    EVENT = "event"
    STABILITY = "stability"
    PORTAL = "portal"
    EXCEPTIONS = "exceptions"

class HealthAlert(Base):
    __tablename__ = "health_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    source_system = Column(String(100), nullable=False)
    raw_data = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # AI-generated fields
    ai_category = Column(String(100))
    ai_priority = Column(String(50))
    ai_summary = Column(Text)
    ai_recommendation = Column(Text)
    
    # Action tracking
    is_resolved = Column(Boolean, default=False)
    jira_ticket_id = Column(String(50))
    slack_alert_sent = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<HealthAlert(id={self.id}, title='{self.title}', category={self.category}, priority={self.ai_priority})>"