from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api import deps
from app.db.base import BaseRepository
from app.models.action import RemediationAction, ActionStatus
# Import the report generator
from app.services.report_generator import report_generator

# --- THIS LINE IS REQUIRED ---
router = APIRouter()

@router.get("/{incident_id}", response_model=List[RemediationAction])
async def get_actions_for_incident(
    incident_id: str,
    action_repo: BaseRepository = Depends(deps.get_action_repo)
):
    # Retrieve actions for a specific incident
    return await action_repo.get_all(partition_key=incident_id)

@router.post("/{action_id}/approve", response_model=RemediationAction)
async def approve_action(
    action_id: str,
    action_repo: BaseRepository = Depends(deps.get_action_repo),
    incident_repo: BaseRepository = Depends(deps.get_incident_repo)
):
    # 1. Fetch Action
    action = await action_repo.get(action_id, partition_key=action_id)
    if not action:
        # Fallback fetch (incase partition key logic varies)
        action = await action_repo.get(action_id)
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")

    # 2. Update Status to EXECUTED (Skip "Approved" state for faster demo)
    action.status = ActionStatus.EXECUTED
    await action_repo.update(action.id, action.id, {"status": ActionStatus.EXECUTED})
    
    # 3. MILLION DOLLAR FEATURE: Generate Audit Report
    # We fetch the incident to populate the PDF
    incident = await incident_repo.get(action.incident_id, partition_key=action.incident_id)
    
    if incident:
        print(f"📄 Generating Forensic Report for Incident {incident.id}...")
        try:
            pdf_url = report_generator.generate_and_upload(incident, action)
            print(f"✅ REPORT UPLOADED: {pdf_url}")
        except Exception as e:
            print(f"⚠️ Report Generation Failed: {e}")
    else:
        print("⚠️ Could not find incident, skipping report.")

    return action

@router.post("/{action_id}/execute", response_model=RemediationAction)
async def execute_action(
    action_id: str,
    action_repo: BaseRepository = Depends(deps.get_action_repo),
    incident_repo: BaseRepository = Depends(deps.get_incident_repo)
):
    # Alias to approve for compatibility
    return await approve_action(action_id, action_repo, incident_repo)