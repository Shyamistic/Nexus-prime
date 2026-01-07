import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load your .env file
load_dotenv(dotenv_path="backend/.env")

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

async def list_models():
    if not API_KEY:
        print("❌ No API Key found in .env!")
        return

    print(f"🔑 Testing Key: {API_KEY[:10]}...")
    
    # We ask the API for the list of models
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            
            if "error" in data:
                print(f"❌ Error: {data['error']['message']}")
            else:
                print("\n✅ AVAILABLE MODELS:")
                found_any = False
                for model in data.get('models', []):
                    # We only care about models that can 'generateContent'
                    if "generateContent" in model['supportedGenerationMethods']:
                        print(f"  - {model['name']}")
                        found_any = True
                
                if not found_any:
                    print("⚠️ No content generation models found. Check API enablement.")

if __name__ == "__main__":
    asyncio.run(list_models())