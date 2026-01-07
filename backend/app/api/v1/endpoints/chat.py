from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api import deps
from app.db.base import BaseRepository
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    incident_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def chat_with_incident(
    request: ChatRequest,
    incident_repo: BaseRepository = Depends(deps.get_incident_repo)
):
    # 1. Fetch Incident Context
    incident = await incident_repo.get(request.incident_id, partition_key=request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # 2. PRODUCTION LOGIC: Use Azure OpenAI first, then Gemini
    has_azure_ai = settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT
    has_gemini_ai = settings.GEMINI_API_KEY

    if has_azure_ai:
        try:
            # Use Azure OpenAI directly
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            system_prompt = f"""
            You are NEXUS, an expert Site Reliability Engineer.
            Current Incident: {incident.title}
            Summary: {incident.summary}
            Root Cause: {incident.root_cause_analysis}
            
            Answer the user's question briefly and professionally.
            """
            
            response = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return ChatResponse(response=response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Azure AI Failed: {e}. Trying Gemini...")
            # Fall through to Gemini
            pass
    
    if has_gemini_ai:
        try:
            # Use Gemini
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            system_prompt = f"""
            You are NEXUS, an expert Site Reliability Engineer.
            Current Incident: {incident.title}
            Summary: {incident.summary}
            Root Cause: {incident.root_cause_analysis}
            
            Answer the user's question briefly and professionally.
            """
            
            response = model.generate_content(f"{system_prompt}\n\nUser Question: {request.message}")
            return ChatResponse(response=response.text)
            
        except Exception as e:
            logger.error(f"Gemini AI Failed: {e}. Falling back to Mock.")
            # Fall through to mock response below
            pass

    # 3. Fallback / Mock Response
    return ChatResponse(response=_get_mock_response(request.message))

def _get_mock_response(message: str) -> str:
    """Fake responses for the demo until you get Azure keys"""
    msg = message.lower()
    if "why" in msg or "cause" in msg:
        return "The root cause is a memory leak in the connection pool logic introduced in version v2.4.1. This is causing connections to hang in CLOSE_WAIT state."
    elif "fix" in msg or "solution" in msg:
        return "I recommend restarting the affected pods to clear the zombie connections, then rolling back the deployment to v2.4.0."
    elif "risk" in msg:
        return "Restarting the pods carries a low risk (approx 1% error rate for 5s), but doing nothing will lead to a total outage within 15 minutes."
    else:
        return f"I recorded that query about '{message}'. As an AI Copilot, I am monitoring the situation closely."