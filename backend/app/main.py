from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio

# --- AZURE MONITOR INTEGRATION ---
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    AZURE_MONITOR_AVAILABLE = True
except ImportError:
    AZURE_MONITOR_AVAILABLE = False
    print("Azure Monitor not available - install azure-monitor-opentelemetry")

# --- AZURE STORAGE INTEGRATION ---
from azure.storage.blob import BlobServiceClient

from app.core.config import settings
from app.core.state import db_state
from app.api.v1.api import api_router
from app.db.cosmos import CosmosRepository
from app.db.mock_cosmos import MockCosmosRepository
from app.models.incident import Incident
from app.models.event import IncidentEvent
from app.models.action import RemediationAction
from app.models.user import User, Tenant, UserInvitation, UsageMetrics

# Import services
from app.services.rca_engine import rca_engine
from app.services.websocket_manager import ws_manager

# Add startup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Azure Monitor
if settings.APPLICATIONINSIGHTS_CONNECTION_STRING and AZURE_MONITOR_AVAILABLE:
    try:
        configure_azure_monitor(
            connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING
        )
        print("✅ Azure Monitor: CONNECTED (Live Metrics Enabled)")
    except Exception as e:
        print(f"⚠️ Azure Monitor Error: {e}")
else:
    if not settings.APPLICATIONINSIGHTS_CONNECTION_STRING:
        print("⚠️ Azure Monitor: DISABLED (No Connection String)")
    else:
        print("⚠️ Azure Monitor: DISABLED (Package not available)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifecycle Manager.
    - Connects to Cosmos DB
    - Initializes Blob Storage for Reports
    - Starts WebSocket heartbeat
    """
    # Startup
    if settings.is_mock_mode():
        logger.info("\n" + "="*60)
        logger.info("⚠️  WARNING: RUNNING IN MOCK MODE")
        logger.info("="*60 + "\n")
        
        db_state.incidents = MockCosmosRepository("incidents", Incident)
        db_state.events = MockCosmosRepository("events", IncidentEvent)
        db_state.actions = MockCosmosRepository("actions", RemediationAction)
        db_state.users = MockCosmosRepository("users", User)
        db_state.tenants = MockCosmosRepository("tenants", Tenant)
        db_state.invitations = MockCosmosRepository("invitations", UserInvitation)
        db_state.usage = MockCosmosRepository("usage", UsageMetrics)
    
    else:
        logger.info(f"\n🚀 CONNECTING TO AZURE COSMOS DB: {settings.COSMOS_ENDPOINT}")
        logger.info(f"🔑 Mock mode: {settings.is_mock_mode()}")
        logger.info(f"🔑 Azure OpenAI available: {bool(settings.AZURE_OPENAI_API_KEY)}")
        logger.info(f"🔑 Gemini available: {bool(settings.GEMINI_API_KEY)}")
        logger.info(f"🔧 RCA Engine provider: {rca_engine.provider}")
        from azure.cosmos.aio import CosmosClient
        from azure.identity import DefaultAzureCredential
        
        credential = DefaultAzureCredential()
        
        db_state.client = CosmosClient(
            url=settings.COSMOS_ENDPOINT, 
            credential=settings.COSMOS_KEY
        )
        
        database = db_state.client.get_database_client(settings.COSMOS_DB_NAME)
        
        # Initialize Real Azure Repositories
        db_state.incidents = CosmosRepository(
            database.get_container_client(settings.CONTAINER_INCIDENTS), Incident
        )
        db_state.events = CosmosRepository(
            database.get_container_client(settings.CONTAINER_EVENTS), IncidentEvent
        )
        db_state.actions = CosmosRepository(
            database.get_container_client(settings.CONTAINER_ACTIONS), RemediationAction
        )
        db_state.users = CosmosRepository(
            database.get_container_client("users"), User
        )
        db_state.tenants = CosmosRepository(
            database.get_container_client("tenants"), Tenant
        )
        db_state.invitations = CosmosRepository(
            database.get_container_client("invitations"), UserInvitation
        )
        db_state.usage = CosmosRepository(
            database.get_container_client("usage"), UsageMetrics
        )

        # --- NEW: INITIALIZE BLOB STORAGE CONTAINER ---
        if settings.AZURE_STORAGE_CONNECTION_STRING:
            try:
                print("📦 CONNECTING TO AZURE BLOB STORAGE...")
                blob_service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
                container = blob_service.get_container_client(settings.CONTAINER_REPORTS)
                
                # Check if container exists
                container.get_container_properties()
                print(f"✅ Storage Container Found: {settings.CONTAINER_REPORTS}")
            except Exception as e:
                print(f"⚠️ Blob Storage Error: {e}")
    
    # Start WebSocket heartbeat
    heartbeat_task = asyncio.create_task(ws_manager.start_heartbeat())
    
    yield # App runs here
    
    # Shutdown
    heartbeat_task.cancel()
    if db_state.client:
        print("Closing Database Connections...")
        await db_state.client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)



# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = websocket.query_params.get("client_id")
    await ws_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Listen for messages from client
            message = await websocket.receive_text()
            await ws_manager.handle_client_message(websocket, message)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# WebSocket stats endpoint
@app.get("/ws/stats")
async def websocket_stats():
    return ws_manager.get_connection_stats()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "services": {
            "rca_engine": "operational",
            "database": "operational",
            "storage": "operational" if settings.AZURE_STORAGE_CONNECTION_STRING else "disabled",
            "monitoring": "operational" if AZURE_MONITOR_AVAILABLE else "disabled"
        },
        "version": "1.0.0"
    }