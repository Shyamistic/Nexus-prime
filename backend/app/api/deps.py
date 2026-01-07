from app.core.state import db_state # CHANGED: Imported from core.state
from app.db.base import BaseRepository # Ensure this uses the Base class we fixed earlier
from app.services.user_service import UserService

async def get_incident_repo() -> BaseRepository:
    return db_state.incidents

async def get_event_repo() -> BaseRepository:
    return db_state.events

async def get_action_repo() -> BaseRepository:
    return db_state.actions

async def get_user_repo() -> BaseRepository:
    return db_state.users

async def get_tenant_repo() -> BaseRepository:
    return db_state.tenants

async def get_invitation_repo() -> BaseRepository:
    return db_state.invitations

async def get_usage_repo() -> BaseRepository:
    return db_state.usage

async def get_user_service() -> UserService:
    user_repo = await get_user_repo()
    tenant_repo = await get_tenant_repo()
    invitation_repo = await get_invitation_repo()
    usage_repo = await get_usage_repo()
    
    return UserService(
        user_repo=user_repo,
        tenant_repo=tenant_repo,
        invitation_repo=invitation_repo,
        usage_repo=usage_repo
    )