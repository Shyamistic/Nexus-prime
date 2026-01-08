from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS Incident Copilot"
    API_V1_STR: str = "/api/v1"
    
    # Security settings
    SECRET_KEY: Optional[str] = None
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200 # 30 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60
    
    # AI & DB Keys (Keep your existing ones)
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4-turbo"
    AZURE_OPENAI_API_VERSION: str = "2023-12-01-preview"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    COSMOS_ENDPOINT: Optional[str] = None
    COSMOS_KEY: Optional[str] = None
    COSMOS_DB_NAME: str = "nexus-db"
    CONTAINER_INCIDENTS: str = "incidents"
    CONTAINER_EVENTS: str = "events"
    CONTAINER_SERVICES: str = "services"
    CONTAINER_ACTIONS: str = "actions"

    # --- NEW ADDITION ---
    APPLICATIONINSIGHTS_CONNECTION_STRING: Optional[str] = None
    # NEW
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    CONTAINER_REPORTS: str = "incident-reports"
    
    # Notification settings
    SLACK_WEBHOOK_URL: Optional[str] = None
    TEAMS_WEBHOOK_URL: Optional[str] = None
    
    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    EMAIL_RECIPIENTS: str = "sre-team@company.com,on-call@company.com"
    
    # SMS settings (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    SMS_RECIPIENTS: str = "+1234567890"
    
    # SMS settings (AWS SNS)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SNS_REGION: str = "us-east-1"
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_IDS: str = ""
    
    # Remediation settings
    REMEDIATION_ENABLED: bool = True
    REMEDIATION_DRY_RUN: bool = True
    
    # Incident management settings
    INCIDENT_AUTO_RESOLVE_HOURS: int = 24
    INCIDENT_ESCALATION_MINUTES: int = 30
    DEDUPLICATION_ENABLED: bool = True
    DEDUPLICATION_SIMILARITY_THRESHOLD: float = 0.8
    DEDUPLICATION_TIME_WINDOW_HOURS: int = 24
    
    USE_MOCK_SERVICES: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def is_mock_mode(self) -> bool:
        # Run Real Mode if ANY AI key is present
        has_azure = self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_API_KEY
        has_standard = self.OPENAI_API_KEY is not None
        has_gemini = self.GEMINI_API_KEY is not None
        
        if self.USE_MOCK_SERVICES: return True
        return not (has_azure or has_standard or has_gemini)

settings = Settings()