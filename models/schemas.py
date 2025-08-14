from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class HealthCategory(str, Enum):
    OPTIMIZER = "optimizer"
    SECURITY = "security"
    LIMITS = "limits"
    EVENT = "event"
    STABILITY = "stability"
    PORTAL = "portal"
    EXCEPTIONS = "exceptions"

class HealthAlertBase(BaseModel):
    title: str
    description: str
    category: HealthCategory
    source_system: str
    raw_data: Optional[str] = None

class HealthAlertCreate(HealthAlertBase):
    pass

class HealthAlertUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[HealthCategory] = None
    source_system: Optional[str] = None
    raw_data: Optional[str] = None
    ai_category: Optional[str] = None
    ai_priority: Optional[PriorityLevel] = None
    ai_summary: Optional[str] = None
    ai_recommendation: Optional[str] = None
    is_resolved: Optional[bool] = None
    jira_ticket_id: Optional[str] = None
    slack_alert_sent: Optional[bool] = None

class HealthAlert(HealthAlertBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    ai_category: Optional[str] = None
    ai_priority: Optional[PriorityLevel] = None
    ai_summary: Optional[str] = None
    ai_recommendation: Optional[str] = None
    is_resolved: bool = False
    jira_ticket_id: Optional[str] = None
    slack_alert_sent: bool = False

    class Config:
        from_attributes = True

class HealthAlertCategorization(BaseModel):
    """Model for AI categorization result"""
    category: str = Field(description="The most appropriate category for this health alert")
    priority: PriorityLevel = Field(description="The priority level for this health alert")
    summary: str = Field(description="A concise summary of the health alert")
    recommendation: str = Field(description="A recommended action to resolve the health alert")
    
    # Simple configuration for Pydantic v2 without examples
    model_config = {
        "json_schema_extra": {}
    }