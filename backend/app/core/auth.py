from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import secrets
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuration - FIXED: Use environment variables
SECRET_KEY = settings.SECRET_KEY or secrets.token_urlsafe(32)
JWT_SECRET_KEY = settings.JWT_SECRET_KEY or SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM or "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS or 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None

class UserRole:
    ADMIN = "admin"
    SRE = "sre"
    VIEWER = "viewer"

class AuthService:
    def __init__(self):
        self.pwd_context = pwd_context
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            tenant_id: str = payload.get("tenant_id")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(
                user_id=user_id,
                email=email,
                role=role,
                tenant_id=tenant_id
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def generate_api_key(self, user_id: str, tenant_id: str) -> str:
        """Generate API key for webhook endpoints"""
        key_data = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "type": "api_key",
            "created_at": datetime.utcnow().isoformat()
        }
        return jwt.encode(key_data, JWT_SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_api_key(self, api_key: str) -> TokenData:
        """Verify API key"""
        try:
            payload = jwt.decode(api_key, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "api_key":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            
            return TokenData(
                user_id=payload.get("sub"),
                tenant_id=payload.get("tenant_id")
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

# Global auth service instance
auth_service = AuthService()

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current authenticated user"""
    return auth_service.verify_token(credentials.credentials)

async def get_current_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_current_sre(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require SRE or admin role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SRE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SRE access required"
        )
    return current_user

async def verify_api_key_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify API key for webhook endpoints"""
    return auth_service.verify_api_key(credentials.credentials)

# Rate limiting decorator
from functools import wraps
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        
        if len(self.requests[key]) >= limit:
            return False
        
        self.requests[key].append(now)
        return True

# Simple auth function for demo
async def get_current_user_simple():
    """Simple auth for demo - returns mock user"""
    return type('User', (), {
        'id': 'demo_user',
        'email': 'demo@nexus.com',
        'tenant_id': 'demo_tenant',
        'role': 'admin'
    })()

def rate_limit(limit: int = 100, window: int = 3600):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user/tenant info for rate limiting
            current_user = kwargs.get('current_user')
            if current_user:
                key = f"{current_user.tenant_id}:{current_user.user_id}"
            else:
                key = "anonymous"
            
            if not rate_limiter.is_allowed(key, limit, window):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator