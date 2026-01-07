from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ActionType(str, Enum):
    RESTART_POD = "restart_pod"
    SCALE_SERVICE = "scale_service"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    CLEAR_CACHE = "clear_cache"
    BLOCK_IP = "block_ip"

class ActionStatus(str, Enum):
    PROPOSED = "proposed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXECUTED = "executed"  # <--- CRITICAL FOR THE PDF GENERATION

class RemediationAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    action_type: ActionType
    title: str
    reasoning: str
    status: ActionStatus = ActionStatus.PROPOSED
    parameters: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None