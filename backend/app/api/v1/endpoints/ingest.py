import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.api import deps
from app.models.incident import Incident, IncidentStatus, SeverityLevel
from app.models.event import IncidentEvent
from app.db.base import BaseRepository
from app.services.rca_engine import rca_engine

router = APIRouter()
logger = logging.getLogger(__name__)

# Universal Alert Schema
class AlertPayload(BaseModel):
    title: str
    description: str
    severity: Optional[str] = "medium"
    source: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    timestamp: Optional[datetime] = None

# Platform-specific schemas
class DatadogAlert(BaseModel):
    title: str
    body: str
    alert_type: str = "error"
    tags: List[str] = []
    priority: Optional[str] = None

class PagerDutyAlert(BaseModel):
    incident: Dict[str, Any]
    
class PrometheusAlert(BaseModel):
    alerts: List[Dict[str, Any]]
    
class GenericWebhook(BaseModel):
    title: str
    message: str
    severity: Optional[str] = "medium"
    source: Optional[str] = "generic"
    tags: List[str] = []
    
# Severity mapping
SEVERITY_MAP = {
    "critical": SeverityLevel.SEV1,
    "high": SeverityLevel.SEV1, 
    "error": SeverityLevel.SEV2,
    "medium": SeverityLevel.SEV2,
    "warning": SeverityLevel.SEV3,
    "low": SeverityLevel.SEV3,
    "info": SeverityLevel.SEV4
}

async def _create_incident_from_alert(
    alert: AlertPayload,
    incident_repo: BaseRepository,
    event_repo: BaseRepository,
    background_tasks: BackgroundTasks
) -> str:
    """Core incident creation logic"""
    incident_id = str(uuid.uuid4())
    
    # Map severity
    severity = SEVERITY_MAP.get(alert.severity.lower(), SeverityLevel.SEV2)
    
    incident = Incident(
        id=incident_id,
        title=alert.title,
        summary=alert.description,
        severity=severity,
        status=IncidentStatus.OPEN,
        created_at=alert.timestamp or datetime.utcnow(),
        tags=alert.tags
    )
    
    event = IncidentEvent(
        id=str(uuid.uuid4()),
        incident_id=incident_id,
        description=f"Alert from {alert.source}: {alert.description}",
        source=alert.source,
        event_type="alert",
        payload=alert.metadata,
        created_at=datetime.utcnow()
    )
    
    await incident_repo.create(incident)
    await event_repo.create(event)
    
    background_tasks.add_task(rca_engine.analyze_incident, incident_id, incident_repo, event_repo)
    logger.info(f"🚨 Created incident {incident_id} from {alert.source}")
    
    return incident_id

@router.post("/webhook/datadog", status_code=202)
async def ingest_datadog(
    payload: DatadogAlert,
    background_tasks: BackgroundTasks,
    incident_repo: BaseRepository = Depends(deps.get_incident_repo),
    event_repo: BaseRepository = Depends(deps.get_event_repo),
):
    alert = AlertPayload(
        title=payload.title,
        description=payload.body,
        severity=payload.alert_type,
        source="datadog",
        tags=payload.tags,
        metadata=payload.dict()
    )
    incident_id = await _create_incident_from_alert(alert, incident_repo, event_repo, background_tasks)
    return {"status": "processing", "incident_id": incident_id}

@router.post("/webhook/pagerduty", status_code=202)
async def ingest_pagerduty(
    payload: PagerDutyAlert,
    background_tasks: BackgroundTasks,
    incident_repo: BaseRepository = Depends(deps.get_incident_repo),
    event_repo: BaseRepository = Depends(deps.get_event_repo),
):
    incident_data = payload.incident
    alert = AlertPayload(
        title=incident_data.get("title", "PagerDuty Incident"),
        description=incident_data.get("description", ""),
        severity=incident_data.get("urgency", "medium"),
        source="pagerduty",
        tags=[incident_data.get("service", {}).get("name", "unknown")],
        metadata=payload.dict()
    )
    incident_id = await _create_incident_from_alert(alert, incident_repo, event_repo, background_tasks)
    return {"status": "processing", "incident_id": incident_id}

@router.post("/webhook/prometheus", status_code=202)
async def ingest_prometheus(
    payload: PrometheusAlert,
    background_tasks: BackgroundTasks,
    incident_repo: BaseRepository = Depends(deps.get_incident_repo),
    event_repo: BaseRepository = Depends(deps.get_event_repo),
):
    incidents = []
    for alert_data in payload.alerts:
        alert = AlertPayload(
            title=alert_data.get("labels", {}).get("alertname", "Prometheus Alert"),
            description=alert_data.get("annotations", {}).get("description", ""),
            severity=alert_data.get("labels", {}).get("severity", "medium"),
            source="prometheus",
            tags=list(alert_data.get("labels", {}).keys()),
            metadata=alert_data
        )
        incident_id = await _create_incident_from_alert(alert, incident_repo, event_repo, background_tasks)
        incidents.append(incident_id)
    return {"status": "processing", "incident_ids": incidents}

@router.post("/webhook/generic", status_code=202)
async def ingest_generic(
    payload: GenericWebhook,
    background_tasks: BackgroundTasks,
    incident_repo: BaseRepository = Depends(deps.get_incident_repo),
    event_repo: BaseRepository = Depends(deps.get_event_repo),
):
    alert = AlertPayload(
        title=payload.title,
        description=payload.message,
        severity=payload.severity,
        source=payload.source,
        tags=payload.tags,
        metadata=payload.dict()
    )
    incident_id = await _create_incident_from_alert(alert, incident_repo, event_repo, background_tasks)
    return {"status": "processing", "incident_id": incident_id}