import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.models.action import RemediationAction, ActionStatus, ActionType
from app.models.incident import IncidentStatus # <--- New Import
from app.db.base import BaseRepository
from app.core.state import db_state # <--- Access to the DB

logger = logging.getLogger(__name__)

class ActionExecutor:
    """
    Safely executes remediation actions on infrastructure.
    """
    
    async def execute_action(
        self, 
        action_id: str, 
        action_repo: BaseRepository
    ) -> RemediationAction:
        
        # 1. Fetch the Action
        action = await action_repo.get(action_id, partition_key=action_id)
        if not action:
            raise ValueError(f"Action {action_id} not found")
            
        if action.status != ActionStatus.APPROVED:
            # If it's already done or not approved, skip
            return action

        # 2. Mark as IN_PROGRESS
        action.status = ActionStatus.IN_PROGRESS
        await action_repo.update(action.id, action.id, {"status": ActionStatus.IN_PROGRESS})
        logger.info(f"Executing action: {action.action_type} on incident {action.incident_id}")

        try:
            # 3. Route to specific handler
            result_log = ""
            if action.action_type == ActionType.RESTART_POD:
                result_log = await self._restart_pod(action.parameters)
            elif action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
                result_log = await self._rollback_deployment(action.parameters)
            else:
                result_log = await self._generic_script_execution(action.parameters)

            # 4. Success
            action.status = ActionStatus.COMPLETED
            action.execution_log = result_log
            
            # --- AUTO-RESOLVE INCIDENT LOGIC ---
            # If action succeeded, mark the incident as RESOLVED
            await self._resolve_incident(action.incident_id)
            # -----------------------------------
            
        except Exception as e:
            # 5. Failure Handling
            logger.error(f"Action failed: {str(e)}")
            action.status = ActionStatus.FAILED
            action.execution_log = f"Error: {str(e)}"
            
        # 6. Save Final Action State
        return await action_repo.update(action.id, action.id, {
            "status": action.status,
            "execution_log": action.execution_log,
            "updated_at": datetime.utcnow().isoformat()
        })

    async def _resolve_incident(self, incident_id: str):
        """Helper to mark incident as RESOLVED"""
        try:
            incident = await db_state.incidents.get(incident_id, incident_id)
            if incident:
                incident.status = IncidentStatus.RESOLVED
                await db_state.incidents.update(incident.id, incident.id, {"status": IncidentStatus.RESOLVED})
                logger.info(f"Auto-resolved incident {incident_id}")
        except Exception as e:
            logger.error(f"Failed to auto-resolve incident: {e}")

    # --- SIMULATED INFRASTRUCTURE HANDLERS ---
    
    async def _restart_pod(self, params: Dict[str, Any]) -> str:
        target = params.get("target", "unknown-pod")
        logger.info(f"Connecting to K8s Cluster... Deleting Pod {target}")
        await asyncio.sleep(3) # Simulate network latency
        return f"SUCCESS: Pod {target} deleted. ReplicaSet created new instance (Age: 2s)."

    async def _rollback_deployment(self, params: Dict[str, Any]) -> str:
        service = params.get("service", "unknown-svc")
        version = params.get("previous_version", "v1.0.0")
        logger.info(f"Rolling back {service} to {version}")
        await asyncio.sleep(5) 
        return f"SUCCESS: Deployment {service} rolled back to {version}. Health checks passed."

    async def _generic_script_execution(self, params: Dict[str, Any]) -> str:
        script = params.get("script_name", "maintenance.sh")
        logger.info(f"Running automation runbook: {script}")
        await asyncio.sleep(2)
        return f"SUCCESS: Script {script} executed with exit code 0."

# Singleton
executor = ActionExecutor()