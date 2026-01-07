import sys
import os
import asyncio
from azure.cosmos.aio import CosmosClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

ENDPOINT = os.getenv("COSMOS_ENDPOINT")
KEY = os.getenv("COSMOS_KEY")
DB_NAME = "nexus-db"

async def wipe():
    print(f"🗑️ Wiping Database: {DB_NAME}...")
    client = CosmosClient(ENDPOINT, credential=KEY)
    db = client.get_database_client(DB_NAME)

    containers = ["incidents", "actions", "events"]
    
    for container_name in containers:
        try:
            container = db.get_container_client(container_name)
            # Delete the container entirely and recreate it (fastest wipe)
            await db.delete_container(container_name)
            print(f"❌ Deleted container: {container_name}")
            
            # Recreate
            await db.create_container(id=container_name, partition_key="/id")
            print(f"✨ Recreated container: {container_name}")
        except Exception as e:
            print(f"⚠️ Error on {container_name}: {e}")

    await client.close()
    print("✅ Database Wiped & Reset.")

if __name__ == "__main__":
    asyncio.run(wipe())