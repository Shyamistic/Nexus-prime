from enum import Enum
from typing import Dict, Any
from .common import NexusBaseModel

class EventSource(str, Enum):
    DATADOG = "datadog"
    PROMETHEUS = "prometheus"
    PAGERDUTY = "pagerduty"
    GENERIC = "generic"
    SYSTEM = "system"

class IncidentEvent(NexusBaseModel):
    incident_id: str
    source: EventSource
    event_type: str
    payload: Dict[str, Any]
    description: str