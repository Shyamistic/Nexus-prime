from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, ValidationError
import logging
import json
from datetime import datetime

from app.models.incident import Incident, SeverityLevel, IncidentStatus
from app.models.event import IncidentEvent, EventType
from app.core.auth import verify_api_key_header, TokenData, rate_limit
from app.services.user_service import UserService
from app.services.deduplication import deduplication_service
from app.services.rca_engine import rca_engine
from app.services.notifications import notification_service
from app.services.websocket_manager import ws_manager
from app.api import deps
from app.db.base import BaseRepository

router = APIRouter()
logger = logging.getLogger(__name__)

# Enhanced webhook payload validation
class WebhookPayload(BaseModel):
    title: str
    summary: Optional[str] = ""
    severity: Optional[str] = "SEV3"
    source: Optional[str] = "generic"
    service_id: Optional[str] = "unknown"
    tags: Optional[list] = []
    metadata: Optional[Dict[str, Any]] = {}

class DatadogPayload(BaseModel):
    title: str
    body: str
    alert_type: str
    tags: list = []
    priority: str = "normal"
    source_type_name: str = "datadog"
    date_happened: Optional[int] = None
    aggregation_key: Optional[str] = None
    alert_id: Optional[int] = None

class PagerDutyPayload(BaseModel):
    messages: list

class PrometheusPayload(BaseModel):
    version: str
    groupKey: str
    status: str
    receiver: str
    groupLabels: Dict[str, Any]
    commonLabels: Dict[str, Any]
    commonAnnotations: Dict[str, Any]
    externalURL: str
    alerts: list

def validate_webhook_payload(payload: Dict[str, Any], source: str) -> WebhookPayload:
    """Validate and normalize webhook payload based on source"""
    try:
        if source == "datadog":
            datadog_payload = DatadogPayload(**payload)
            return WebhookPayload(
                title=datadog_payload.title,
                summary=datadog_payload.body,
                severity=_map_datadog_severity(datadog_payload.alert_type, datadog_payload.priority),
                source="datadog",
                tags=datadog_payload.tags,
                metadata={
                    "alert_id": datadog_payload.alert_id,
                    "aggregation_key": datadog_payload.aggregation_key,
                    "date_happened": datadog_payload.date_happened
                }
            )
        
        elif source == "pagerduty":
            pd_payload = PagerDutyPayload(**payload)
            if not pd_payload.messages:
                raise ValueError("No messages in PagerDuty payload")
            
            incident = pd_payload.messages[0].get("incident", {})
            return WebhookPayload(
                title=incident.get("title", "PagerDuty Incident"),
                summary=incident.get("description", ""),
                severity=_map_pagerduty_severity(incident.get("urgency", "low")),
                source="pagerduty",
                service_id=incident.get("service", {}).get("name", "unknown"),
                metadata={
                    "incident_id": incident.get("id"),
                    "incident_number": incident.get("incident_number"),
                    "status": incident.get("status")
                }
            )
        
        elif source == "prometheus":
            prom_payload = PrometheusPayload(**payload)
            if not prom_payload.alerts:
                raise ValueError("No alerts in Prometheus payload")
            
            alert = prom_payload.alerts[0]
            return WebhookPayload(
                title=alert.get("annotations", {}).get("summary", "Prometheus Alert"),
                summary=alert.get("annotations", {}).get("description", ""),
                severity=_map_prometheus_severity(alert.get("labels", {}).get("severity", "warning")),
                source="prometheus",
                service_id=alert.get("labels", {}).get("job", "unknown"),
                tags=list(alert.get("labels", {}).keys()),
                metadata={
                    "alertname": alert.get("labels", {}).get("alertname"),
                    "instance": alert.get("labels", {}).get("instance"),
                    "fingerprint": alert.get("fingerprint"),
                    "generator_url": alert.get("generatorURL")
                }
            )
        
        else:  # generic
            return WebhookPayload(**payload)
    
    except (ValidationError, ValueError, KeyError) as e:
        logger.error(f"Webhook payload validation failed for {source}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {source} webhook payload: {str(e)}"
        )

def _map_datadog_severity(alert_type: str, priority: str) -> str:
    """Map Datadog alert type and priority to severity"""
    if alert_type == "error" and priority == "high":
        return "SEV1"
    elif alert_type == "error":
        return "SEV2"
    elif alert_type == "warning":
        return "SEV3"
    else:
        return "SEV4"

def _map_pagerduty_severity(urgency: str) -> str:
    """Map PagerDuty urgency to severity"""
    if urgency == "high":
        return "SEV1"
    elif urgency == "medium":
        return "SEV2"
    else:
        return "SEV3"

def _map_prometheus_severity(severity: str) -> str:
    """Map Prometheus severity to our severity levels"""
    severity_map = {
        "critical": "SEV1",
        "high": "SEV1",
        "warning": "SEV2",
        "medium": "SEV2",
        "info": "SEV3",
        "low": "SEV3"
    }
    return severity_map.get(severity.lower(), "SEV3")

@router.post("/webhook/datadog")
@rate_limit(limit=1000, window=3600)  # 1000 requests per hour per tenant
async def datadog_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    auth_data: TokenData = Depends(verify_api_key_header),
    incident_repo: BaseRepository = Depends(deps.get_incident_repo),
    event_repo: BaseRepository = Depends(deps.get_event_repo),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Receive Datadog webhook with authentication and tenant isolation"""
    try:
        # Check tenant limits
        limits = await user_service.check_tenant_limits(auth_data.tenant_id)
        if not limits["within_limits"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Tenant has exceeded usage limits"
            )
        
        # Parse payload
        payload = await request.json()
        validated_payload = validate_webhook_payload(payload, "datadog")
        
        # Create incident with tenant isolation
        incident = await _create_incident_from_webhook(
            validated_payload, 
            auth_data.tenant_id,
            incident_repo, 
            event_repo,
            background_tasks
        )
        
        # Track usage
        await user_service.track_usage(auth_data.tenant_id, "incidents_created")
        await user_service.track_usage(auth_data.tenant_id, "api_calls")
        
        logger.info(f"Datadog incident created: {incident.id} for tenant {auth_data.tenant_id}")
        
        return {
            "status": "success",
            "incident_id": incident.id,
            "message": "Incident created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Datadog webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )

@router.post("/webhook/pagerduty")
@rate_limit(limit=1000, window=3600)
async def pagerduty_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    auth_data: TokenData = Depends(verify_api_key_header),
    incident_repo: BaseRepository = Depends(deps.get_incident_repo),
    event_repo: BaseRepository = Depends(deps.get_event_repo),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Receive PagerDuty webhook with authentication and tenant isolation"""
    try:
        # Check tenant limits
        limits = await user_service.check_tenant_limits(auth_data.tenant_id)
        if not limits["within_limits"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Tenant has exceeded usage limits"
            )
        
        payload = await request.json()
        validated_payload = validate_webhook_payload(payload, "pagerduty")
        
        incident = await _create_incident_from_webhook(
            validated_payload, 
            auth_data.tenant_id,
            incident_repo, 
            event_repo,
            background_tasks
        )
        
        # Track usage
        await user_service.track_usage(auth_data.tenant_id, "incidents_created")
        await user_service.track_usage(auth_data.tenant_id, "api_calls")
        
        logger.info(f"PagerDuty incident created: {incident.id} for tenant {auth_data.tenant_id}")
        
        return {
            "status": "success",
            "incident_id": incident.id,
            "message": "Incident created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PagerDuty webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )

@router.post("/webhook/prometheus")
@rate_limit(limit=1000, window=3600)
async def prometheus_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    auth_data: TokenData = Depends(verify_api_key_header),
    incident_repo: BaseRepository = Depends(deps.get_incident_repo),
    event_repo: BaseRepository = Depends(deps.get_event_repo),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Receive Prometheus AlertManager webhook with authentication and tenant isolation"""
    try:
        # Check tenant limits
        limits = await user_service.check_tenant_limits(auth_data.tenant_id)
        if not limits["within_limits"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Tenant has exceeded usage limits"
            )
        
        payload = await request.json()
        validated_payload = validate_webhook_payload(payload, "prometheus")
        
        incident = await _create_incident_from_webhook(
            validated_payload, 
            auth_data.tenant_id,
            incident_repo, 
            event_repo,
            background_tasks
        )
        
        # Track usage
        await user_service.track_usage(auth_data.tenant_id, "incidents_created")
        await user_service.track_usage(auth_data.tenant_id, "api_calls")
        
        logger.info(f"Prometheus incident created: {incident.id} for tenant {auth_data.tenant_id}")
        
        return {
            "status": "success",
            "incident_id": incident.id,
            "message": "Incident created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prometheus webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )

@router.post("/webhook/generic")
@rate_limit(limit=1000, window=3600)
async def generic_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    auth_data: TokenData = Depends(verify_api_key_header),
    incident_repo: BaseRepository = Depends(deps.get_incident_repo),
    event_repo: BaseRepository = Depends(deps.get_event_repo),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Receive generic webhook with authentication and tenant isolation"""
    try:
        # Check tenant limits
        limits = await user_service.check_tenant_limits(auth_data.tenant_id)
        if not limits["within_limits"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Tenant has exceeded usage limits"
            )
        
        payload = await request.json()
        validated_payload = validate_webhook_payload(payload, "generic")
        
        incident = await _create_incident_from_webhook(
            validated_payload, 
            auth_data.tenant_id,
            incident_repo, 
            event_repo,
            background_tasks
        )
        
        # Track usage
        await user_service.track_usage(auth_data.tenant_id, "incidents_created")
        await user_service.track_usage(auth_data.tenant_id, "api_calls")
        
        logger.info(f"Generic incident created: {incident.id} for tenant {auth_data.tenant_id}")
        
        return {
            "status": "success",
            "incident_id": incident.id,
            "message": "Incident created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generic webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )

async def _create_incident_from_webhook(
    payload: WebhookPayload,
    tenant_id: str,
    incident_repo: BaseRepository,
    event_repo: BaseRepository,
    background_tasks: BackgroundTasks
) -> Incident:
    """Create incident from validated webhook payload with tenant isolation"""
    
    # Check for duplicates within tenant
    is_duplicate, existing_incident = await deduplication_service.check_duplicate(
        payload.title,
        payload.summary,
        tenant_id,  # Tenant-scoped deduplication
        incident_repo
    )
    
    if is_duplicate and existing_incident:
        logger.info(f"Duplicate incident detected, updating existing: {existing_incident.id}")
        
        # Update existing incident
        await incident_repo.update(existing_incident.id, existing_incident.id, {
            "updated_at": datetime.utcnow().isoformat(),
            "duplicate_count": getattr(existing_incident, "duplicate_count", 0) + 1
        })
        
        # Create event for duplicate
        event = IncidentEvent(
            incident_id=existing_incident.id,
            event_type=EventType.DUPLICATE_DETECTED,
            description=f"Duplicate alert received from {payload.source}",
            metadata=payload.metadata,
            tenant_id=tenant_id
        )
        await event_repo.create(event.dict(), partition_key=event.incident_id)
        
        return existing_incident
    
    # Create new incident with tenant isolation
    incident = Incident(
        title=payload.title,
        summary=payload.summary or payload.title,
        severity=SeverityLevel(payload.severity),
        status=IncidentStatus.OPEN,
        source=payload.source,
        service_id=payload.service_id or "unknown",
        tags=payload.tags or [],
        metadata=payload.metadata or {},
        tenant_id=tenant_id  # Critical: tenant isolation
    )
    
    # Save incident
    await incident_repo.create(incident.dict(), partition_key=incident.id)
    
    # Create initial event
    event = IncidentEvent(
        incident_id=incident.id,
        event_type=EventType.CREATED,
        description=f"Incident created from {payload.source} webhook",
        metadata=payload.metadata,
        tenant_id=tenant_id
    )
    await event_repo.create(event.dict(), partition_key=event.incident_id)
    
    # Send immediate notifications
    background_tasks.add_task(
        notification_service.send_incident_notification,
        incident,
        "created"
    )
    
    # Send real-time WebSocket update (tenant-scoped)
    background_tasks.add_task(
        ws_manager.send_incident_update,
        incident.dict(),
        "created",
        tenant_id
    )
    
    # Start AI analysis
    background_tasks.add_task(
        rca_engine.analyze_incident,
        incident.id,
        incident_repo,
        event_repo
    )
    
    logger.info(f"Created incident {incident.id} from {payload.source} webhook for tenant {tenant_id}")
    
    return incident

# Health check endpoint (no auth required)
@router.get("/webhook/health")
async def webhook_health():
    """Health check for webhook endpoints"""
    return {
        "status": "healthy",
        "endpoints": [
            "/webhook/datadog",
            "/webhook/pagerduty", 
            "/webhook/prometheus",
            "/webhook/generic"
        ],
        "authentication": "required",
        "rate_limits": {
            "requests_per_hour": 1000,
            "per_tenant": True
        }
    }