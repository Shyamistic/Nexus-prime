import asyncio
import logging
from app.models.incident import IncidentSeverity
from app.core.state import db_state # CHANGED: Imported from core.state

logger = logging.getLogger(__name__)

class MockRCAEngine:
    async def analyze_incident(self, incident_id: str, incident_repo, event_repo):
        logger.info(f"[MOCK AI] Analyzing incident {incident_id}...")
        
        # Simulate "Thinking" time
        await asyncio.sleep(2)
        
        # Fetch the incident to update it
        incident = await incident_repo.get(incident_id, incident_id)
        if not incident:
            return

        # Hardcoded AI Response for Demo
        updates = {
            "root_cause_analysis": (
                "**ROOT CAUSE IDENTIFIED:**\n"
                "The connection pool to the Primary Database (SQL-East) is exhausted.\n\n"
                "**TECHNICAL DETAIL:**\n"
                "A recent deployment (v2.4.1) introduced a memory leak in the connection handling logic. "
                "Connections remain open in `CLOSE_WAIT` state, eventually hitting the max limit (5000).\n"
            ),
            "impact_scope": ["checkout-service", "inventory-api", "payment-gateway"],
            "severity": IncidentSeverity.SEV2
        }

        # Save to Mock DB
        await incident_repo.update(incident_id, incident_id, updates)
        
        # Generate a fake remediation action
        from app.models.action import RemediationAction, ActionType
        
        action = RemediationAction(
            incident_id=incident_id,
            action_type=ActionType.RESTART_POD,
            parameters={"target": "payment-gateway-v2", "namespace": "prod"},
            reasoning="Restarting the pods will flush the zombie connections and restore service temporarily.",
            risk_assessment="Low. Pods are stateless. 1% downtime during rolling restart."
        )
        
        # Use the db_state we imported from core.state
        await db_state.actions.create(action)
        
        logger.info(f"[MOCK AI] Analysis complete for {incident_id}")

mock_rca_engine = MockRCAEngine()