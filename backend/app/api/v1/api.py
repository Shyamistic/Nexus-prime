from fastapi import APIRouter
from app.api.v1.endpoints import ingest, incidents, actions, chat, dashboard, auth_simple

api_router = APIRouter()

api_router.include_router(auth_simple.router, prefix="/auth", tags=["authentication"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])