from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class UserRole(str, Enum):
    ADMIN = "admin"
    SRE = "sre"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class TenantStatus(str, Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.PENDING
    tenant_id: str
    password_hash: Optional[str] = None
    api_keys: List[str] = Field(default_factory=list)
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Tenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: Optional[str] = None
    status: TenantStatus = TenantStatus.TRIAL
    plan: str = "beta"
    max_users: int = 10
    max_incidents_per_month: int = 1000
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Usage tracking
    current_users: int = 0
    incidents_this_month: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.VIEWER
    tenant_id: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    preferences: Optional[Dict[str, Any]] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus
    tenant_id: str
    last_login: Optional[datetime]
    created_at: datetime
    preferences: Dict[str, Any]

class TenantCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    admin_email: EmailStr
    admin_name: str
    admin_password: str

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    status: Optional[TenantStatus] = None
    max_users: Optional[int] = None
    max_incidents_per_month: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str]
    status: TenantStatus
    plan: str
    max_users: int
    max_incidents_per_month: int
    current_users: int
    incidents_this_month: int
    created_at: datetime
    settings: Dict[str, Any]

class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    key_hash: str
    user_id: str
    tenant_id: str
    permissions: List[str] = Field(default_factory=list)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = Field(default_factory=lambda: ["webhook:create"])
    expires_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    id: str
    name: str
    permissions: List[str]
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class InviteUser(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.VIEWER
    message: Optional[str] = None

class UserInvitation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: UserRole
    tenant_id: str
    invited_by: str
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    is_accepted: bool = False

class AcceptInvitation(BaseModel):
    token: str
    password: str

# Usage tracking models
class UsageMetrics(BaseModel):
    tenant_id: str
    period: str  # "daily", "monthly", "yearly"
    date: datetime
    incidents_created: int = 0
    incidents_resolved: int = 0
    ai_analyses_performed: int = 0
    notifications_sent: int = 0
    api_calls: int = 0
    active_users: int = 0
    
class TenantUsage(BaseModel):
    tenant_id: str
    current_period: UsageMetrics
    limits: Dict[str, int]
    usage_percentage: Dict[str, float]
    is_over_limit: bool = False
    next_reset_date: datetime