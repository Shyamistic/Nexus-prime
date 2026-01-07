from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, field_validator
from datetime import datetime

class SeverityLevel(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"
    SEV4 = "SEV4"

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"

class Incident(BaseModel):
    id: str
    title: str
    summary: str
    severity: SeverityLevel
    status: IncidentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    root_cause_analysis: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_confidence: Optional[float] = None
    resolution_eta: Optional[str] = None
    remediation_steps: List[str] = []
    immediate_actions: List[str] = []
    prevention_measures: List[str] = []
    monitoring_recommendations: List[str] = []
    runbook_suggestions: List[str] = []
    similar_incidents: List[str] = []
    impact_assessment: Optional[str] = None
    impact_scope: List[str] = []
    tags: List[str] = []
    source: Optional[str] = None

    # --- THE FIX IS HERE ---
    @field_validator('tags', mode='before')
    @classmethod
    def sanitize_tags(cls, v: Any) -> List[str]:
        # If DB returns an empty dict {} or None, convert it to []
        if isinstance(v, dict):
            return []
        if v is None:
            return []
        return v
    
    @field_validator('remediation_steps', 'immediate_actions', 'prevention_measures', 
                    'monitoring_recommendations', 'runbook_suggestions', 'similar_incidents', 
                    'impact_scope', mode='before')
    @classmethod
    def sanitize_lists(cls, v: Any) -> List[str]:
        # If DB returns an empty dict {} or None, convert it to []
        if isinstance(v, dict):
            return []
        if v is None:
            return []
        # If it's a string, split by comma and strip whitespace
        if isinstance(v, str):
            if not v.strip():
                return []
            return [item.strip() for item in v.split(',') if item.strip()]
        return v