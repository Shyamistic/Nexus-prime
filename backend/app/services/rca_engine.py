# backend/app/services/rca_engine.py

import json
import logging
from typing import Dict, Any
from datetime import datetime

from openai import AzureOpenAI
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from app.core.config import settings

logger = logging.getLogger(__name__)

# =========================================================
# PROVIDER SELECTION
# =========================================================
# Dynamic provider selection based on available credentials
def get_provider():
    if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
        return "azure"
    elif settings.GEMINI_API_KEY:
        return "google"
    else:
        return "mock"

PROVIDER = get_provider()


class RCAEngine:
    def __init__(self):
        self.provider = PROVIDER
        self.azure_client = None
        
        logger.info(f"🔧 Initializing RCA Engine with provider: {PROVIDER}")
        logger.info(f"🔑 Azure OpenAI Key present: {bool(settings.AZURE_OPENAI_API_KEY)}")
        logger.info(f"🔑 Azure OpenAI Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        logger.info(f"🔑 Gemini Key present: {bool(settings.GEMINI_API_KEY)}")

        # -------------------------------
        # AZURE OPENAI (PRIMARY)
        # -------------------------------
        if self.provider == "azure":
            try:
                if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
                    logger.error("❌ Azure OpenAI credentials missing")
                    self.provider = "google"
                else:
                    self.azure_client = AzureOpenAI(
                        api_key=settings.AZURE_OPENAI_API_KEY,
                        api_version=settings.AZURE_OPENAI_API_VERSION,
                        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
                    )
                    logger.info(
                        f"✅ RCA Engine connected to Azure OpenAI "
                        f"(deployment={settings.AZURE_OPENAI_DEPLOYMENT_NAME})"
                    )
            except Exception as e:
                logger.error(f"❌ Azure OpenAI init failed: {e}")
                self.provider = "google"

        # -------------------------------
        # GEMINI (FALLBACK)
        # -------------------------------
        if self.provider == "google" and genai:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                logger.warning("⚠️ Falling back to Google Gemini")
            except Exception as e:
                logger.error(f"❌ Gemini init failed: {e}")
                self.provider = "mock"

        if self.provider == "mock":
            logger.warning("⚠️ RCA Engine running in MOCK mode")

    # =========================================================
    # PUBLIC ENTRYPOINT
    # =========================================================
    def analyze(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"🧠 Starting RCA using {self.provider.upper()}")
        logger.info(f"📊 Incident title: {incident_data.get('title', 'Unknown')}")

        prompt = self._build_prompt(incident_data)
        logger.info(f"📝 Prompt built, length: {len(prompt)} characters")

        if self.provider == "azure":
            logger.info("🚀 Using Azure OpenAI provider")
            return self._analyze_with_azure(prompt)

        if self.provider == "google":
            logger.info("🚀 Using Google Gemini provider")
            return self._analyze_with_gemini(prompt)

        logger.warning("⚠️ Using mock provider")
        return self._analyze_mock()

    # =========================================================
    # AZURE OPENAI IMPLEMENTATION
    # =========================================================
    def _analyze_with_azure(self, prompt: str) -> Dict[str, Any]:
        try:
            logger.info(f"🚀 Calling Azure OpenAI with model {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
            response = self.azure_client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior Site Reliability Engineer. "
                            "Analyze incidents and respond ONLY in valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.25,
                max_tokens=900,
            )

            raw = response.choices[0].message.content
            logger.info(f"✅ Azure OpenAI response received: {len(raw)} characters")
            result = self._parse_json(raw)
            logger.info(f"✅ JSON parsed successfully")
            return result

        except Exception as e:
            logger.error(f"⚠️ Azure inference failed: {e}")
            logger.error(f"🔄 Falling back to mock analysis")
            return self._analyze_mock()

    # =========================================================
    # GEMINI IMPLEMENTATION
    # =========================================================
    def _analyze_with_gemini(self, prompt: str) -> Dict[str, Any]:
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return self._parse_json(response.text)
        except Exception as e:
            logger.error(f"⚠️ Gemini inference failed: {e}")
            return self._analyze_mock()

    # =========================================================
    # PROMPT
    # =========================================================
    def _build_prompt(self, data: Dict[str, Any]) -> str:
        safe_data = json.loads(
            json.dumps(
                data,
                default=str  # 👈 THIS IS THE FIX
            )
        )

        return f"""
You are an expert Site Reliability Engineer analyzing a production incident. Provide a comprehensive root cause analysis and actionable remediation plan.

INCIDENT DETAILS:
{json.dumps(safe_data, indent=2)}

PROVIDE ANALYSIS IN THIS EXACT JSON FORMAT:
{{
  "root_cause": "Detailed technical root cause analysis",
  "impact_assessment": "Business and technical impact description",
  "immediate_actions": [
    "Step 1: Immediate action to take",
    "Step 2: Next immediate action"
  ],
  "remediation_steps": [
    "Step 1: Detailed remediation step",
    "Step 2: Next remediation step"
  ],
  "prevention_measures": [
    "Measure 1: How to prevent this in future",
    "Measure 2: Additional prevention measure"
  ],
  "monitoring_recommendations": [
    "Monitor 1: What to monitor going forward",
    "Monitor 2: Additional monitoring"
  ],
  "estimated_resolution_time": "X hours/minutes",
  "confidence_score": 0.85,
  "similar_incidents": [
    "Pattern 1: Similar incident pattern to watch for",
    "Pattern 2: Related issue pattern"
  ],
  "runbook_suggestions": [
    "Create runbook for: Specific scenario",
    "Update runbook for: Related process"
  ]
}}

Focus on actionable, specific technical recommendations. Be concise but thorough.
"""

    # =========================================================
    # JSON PARSER
    # =========================================================
    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            cleaned = text.strip()
            if "```" in cleaned:
                cleaned = cleaned.split("```")[1]
                cleaned = cleaned.replace("json", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"❌ JSON parse failed: {e}")
            return self._analyze_mock()

    # =========================================================
    # BACKGROUND TASK ENTRYPOINT (ASYNC)
    # =========================================================
    async def analyze_incident(self, incident_id, incident_repo, event_repo):
        """
        Background-task entrypoint.
        Fetches incident data, then runs core analysis.
        """
        logger.info(f"🔍 Starting RCA analysis for incident {incident_id}")

        incident = await incident_repo.get(incident_id, partition_key=incident_id)
        if not incident:
            logger.warning(f"Incident {incident_id} not found")
            return

        logger.info(f"📊 Analyzing incident: {incident.title}")
        incident_data = incident.dict()

        # Run RCA
        try:
            result = self.analyze(incident_data)
            logger.info(f"✅ RCA analysis completed for {incident_id}")
            logger.info(f"🔍 Root cause: {result.get('root_cause', 'Unknown')[:100]}...")
        except Exception as e:
            logger.error(f"❌ RCA analysis failed for {incident_id}: {e}")
            result = self._analyze_mock()

        # Persist results and progress status
        try:
            from app.models.incident import IncidentStatus
            import asyncio
            
            # Enhanced update with more fields
            update_data = {
                "status": IncidentStatus.INVESTIGATING.value,
                "ai_summary": result.get("root_cause", "Analysis completed"),
                "ai_confidence": result.get("confidence_score", 0.8),
                "resolution_eta": result.get("estimated_resolution_time", "Unknown"),
                "remediation_steps": result.get("remediation_steps", []),
                "immediate_actions": result.get("immediate_actions", []),
                "prevention_measures": result.get("prevention_measures", []),
                "monitoring_recommendations": result.get("monitoring_recommendations", []),
                "runbook_suggestions": result.get("runbook_suggestions", []),
                "similar_incidents": result.get("similar_incidents", []),
                "impact_assessment": result.get("impact_assessment", ""),
                "root_cause_analysis": result.get("root_cause"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await incident_repo.update(incident_id, incident_id, update_data)
            logger.info(f"💾 Updated incident {incident_id} with RCA results")
            logger.info(f"🎯 Confidence: {result.get('confidence_score', 0.8):.2f}")
            logger.info(f"⏱️ Estimated resolution: {result.get('estimated_resolution_time', 'Unknown')}")
            
            # Send notification about analysis completion
            try:
                from app.services.notifications import notification_service
                from app.services.websocket_manager import ws_manager
                
                updated_incident = await incident_repo.get(incident_id, partition_key=incident_id)
                
                # Send traditional notifications
                await notification_service.send_incident_notification(updated_incident, "analyzed")
                logger.info(f"📧 Sent analysis notification for incident {incident_id}")
                
                # Send real-time WebSocket update
                await ws_manager.send_incident_update(
                    updated_incident.dict(), 
                    "analysis_completed"
                )
                logger.info(f"🔄 Sent real-time update for incident {incident_id}")
                
            except Exception as e:
                logger.error(f"Failed to send analysis notification: {e}")
            
            # Don't start automatic remediation - wait for manual approval
            # asyncio.create_task(self._start_remediation_pipeline(incident_id, incident_repo, result))
                
        except Exception as e:
            logger.error(f"❌ Failed to update incident {incident_id}: {e}")

    # =========================================================
    # REMEDIATION PIPELINE
    # =========================================================
    async def _start_remediation_pipeline(self, incident_id: str, incident_repo, rca_result: Dict[str, Any]):
        """Start automated remediation pipeline"""
        import asyncio
        from datetime import datetime
        from app.models.incident import IncidentStatus
        
        logger.info(f"🔧 Starting remediation pipeline for incident {incident_id}")
        
        # Wait 30 seconds before starting remediation
        await asyncio.sleep(30)
        
        try:
            # Update status to MITIGATED and execute remediation
            await incident_repo.update(incident_id, incident_id, {
                "status": IncidentStatus.MITIGATED.value,
                "updated_at": datetime.utcnow().isoformat()
            })
            logger.info(f"🔧 Incident {incident_id} status updated to MITIGATED")
            
            # Send mitigation notification immediately
            try:
                from app.services.notifications import notification_service
                from app.services.websocket_manager import ws_manager
                
                incident = await incident_repo.get(incident_id, partition_key=incident_id)
                await notification_service.send_incident_notification(incident, "mitigated")
                await ws_manager.send_incident_update(incident.dict(), "mitigated")
                logger.info(f"📧 Sent mitigation notification for incident {incident_id}")
            except Exception as e:
                logger.error(f"Failed to send mitigation notification: {e}")
            
            # Execute real remediation steps
            try:
                from app.services.real_remediation import remediation_service
                remediation_result = await remediation_service.execute_remediation_steps(
                    incident_id, 
                    rca_result.get("remediation_steps", [])
                )
                
                # Update incident with remediation results
                await incident_repo.update(incident_id, incident_id, {
                    "remediation_executed": True,
                    "remediation_results": remediation_result,
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                logger.info(f"🔧 Remediation completed: {remediation_result['successful_steps']}/{remediation_result['total_steps']} steps successful")
                
            except Exception as e:
                logger.error(f"Failed to execute remediation: {e}")
            
            # Send mitigation notification
            try:
                from app.services.notifications import notification_service
                from app.services.websocket_manager import ws_manager
                
                incident = await incident_repo.get(incident_id, partition_key=incident_id)
                
                # Send traditional notifications
                await notification_service.send_incident_notification(incident, "mitigated")
                
                # Send real-time WebSocket update
                await ws_manager.send_incident_update(
                    incident.dict(), 
                    "mitigated"
                )
                
            except Exception as e:
                logger.error(f"Failed to send mitigation notification: {e}")
            
            # Wait another 60 seconds before resolving
            await asyncio.sleep(60)
            
            # Update status to RESOLVED with resolution summary
            resolution_time = datetime.utcnow()
            
            # Calculate actual resolution time
            incident = await incident_repo.get(incident_id, partition_key=incident_id)
            if incident:
                resolution_duration = resolution_time - incident.created_at
                resolution_hours = resolution_duration.total_seconds() / 3600
            else:
                resolution_hours = 0
            
            await incident_repo.update(incident_id, incident_id, {
                "status": IncidentStatus.RESOLVED.value,
                "resolved_at": resolution_time.isoformat(),
                "actual_resolution_time_hours": resolution_hours,
                "updated_at": resolution_time.isoformat()
            })
            logger.info(f"✅ Incident {incident_id} status updated to RESOLVED (took {resolution_hours:.2f} hours)")
            
            # Send resolution notification
            try:
                from app.services.notifications import notification_service
                from app.services.websocket_manager import ws_manager
                
                incident = await incident_repo.get(incident_id, partition_key=incident_id)
                
                # Send traditional notifications
                await notification_service.send_incident_notification(incident, "resolved")
                
                # Send real-time WebSocket update
                await ws_manager.send_incident_update(
                    incident.dict(), 
                    "resolved"
                )
                
                # Send system alert about resolution
                await ws_manager.send_system_alert(
                    "incident_resolved",
                    f"Incident {incident.title} has been resolved",
                    "success"
                )
                
            except Exception as e:
                logger.error(f"Failed to send resolution notification: {e}")
                
        except Exception as e:
            logger.error(f"❌ Remediation pipeline failed for {incident_id}: {e}")

    # =========================================================
    # MOCK FALLBACK
    # =========================================================
    def _analyze_mock(self) -> Dict[str, Any]:
        return {
            "root_cause": "Database connection pool exhaustion due to increased traffic and inefficient query patterns",
            "impact_assessment": "15% error rate affecting user authentication and payment processing",
            "immediate_actions": [
                "Restart database connection pool",
                "Scale database read replicas"
            ],
            "remediation_steps": [
                "Optimize slow queries identified in logs",
                "Increase connection pool size",
                "Implement connection pooling best practices"
            ],
            "prevention_measures": [
                "Add database connection monitoring",
                "Implement query performance alerts",
                "Regular database performance reviews"
            ],
            "monitoring_recommendations": [
                "Monitor connection pool utilization",
                "Track query execution times",
                "Alert on connection timeouts"
            ],
            "estimated_resolution_time": "2-4 hours",
            "confidence_score": 0.85,
            "similar_incidents": [
                "Database timeout incidents during peak traffic",
                "Connection pool exhaustion patterns"
            ],
            "runbook_suggestions": [
                "Create runbook for: Database connection issues",
                "Update runbook for: Traffic spike response"
            ]
        }


# Singleton
rca_engine = RCAEngine()

# Test initialization
logger.info(f"🎆 RCA Engine initialized with provider: {rca_engine.provider}")
