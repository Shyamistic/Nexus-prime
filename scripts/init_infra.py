import sys
import os
import asyncio
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey  # <--- CRITICAL IMPORT
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Config
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DB_NAME = "nexus-db"
CONTAINERS = ["incidents", "events", "actions"]

STORAGE_CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER = "incident-reports"

async def init_cosmos():
    print(f"🚀 Initializing Cosmos DB: {DB_NAME}")
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        print("❌ Error: Missing Cosmos DB Credentials in .env")
        return

    client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    
    # 1. Create Database if not exists
    try:
        db = await client.create_database_if_not_exists(id=DB_NAME)
        print(f"✅ Database Ready: {DB_NAME}")
    except Exception as e:
        print(f"❌ Failed to create DB: {e}")
        await client.close()
        return

    # 2. Create Containers
    db_client = client.get_database_client(DB_NAME)
    for name in CONTAINERS:
        try:
            # FIX: Use the PartitionKey Object, not just a string
            await db_client.create_container_if_not_exists(
                id=name, 
                partition_key=PartitionKey(path="/id")
            )
            print(f"✅ Container Ready: {name}")
        except Exception as e:
            print(f"❌ Container Error ({name}): {e}")

    await client.close()

def init_storage():
    if not STORAGE_CONN_STR:
        print("⚠️ No Storage Connection String found. Skipping Blob Setup.")
        return

    print(f"\n📦 Initializing Blob Storage: {BLOB_CONTAINER}")
    try:
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONN_STR)
        container = blob_service.get_container_client(BLOB_CONTAINER)
        
        if not container.exists():
            container.create_container(public_access="blob")
            print(f"✅ Created Blob Container: {BLOB_CONTAINER}")
        else:
            print(f"✅ Blob Container Exists: {BLOB_CONTAINER}")
            
    except Exception as e:
        print(f"❌ Storage Error: {e}")

if __name__ == "__main__":
    # Run Storage Sync
    init_storage()
    
    # Run Cosmos Sync
    asyncio.run(init_cosmos())
    
    print("\n🎉 Infrastructure Initialization Complete.")