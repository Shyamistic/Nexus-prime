from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import secrets

router = APIRouter()

class TenantRegister(BaseModel):
    name: str
    admin_email: str
    admin_name: str
    admin_password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# Simple in-memory storage for demo (replace with DB in production)
demo_users = {}

@router.post("/register-tenant")
async def register_tenant_simple(data: TenantRegister):
    """Simple tenant registration for demo purposes"""
    
    # Generate IDs
    tenant_id = f"tenant_{secrets.token_hex(8)}"
    user_id = f"user_{secrets.token_hex(8)}"
    api_key = f"nexus_{secrets.token_urlsafe(32)}"
    access_token = f"token_{secrets.token_urlsafe(32)}"
    
    # Store user for login
    demo_users[data.admin_email] = {
        "id": user_id,
        "email": data.admin_email,
        "full_name": data.admin_name,
        "password": data.admin_password,  # In production, hash this
        "role": "admin",
        "tenant_id": tenant_id
    }
    
    return {
        "message": "Tenant registered successfully",
        "tenant_id": tenant_id,
        "access_token": access_token,
        "refresh_token": f"refresh_{secrets.token_urlsafe(32)}",
        "token_type": "bearer",
        "expires_in": 1800,
        "api_key": api_key,
        "user": {
            "id": user_id,
            "email": data.admin_email,
            "full_name": data.admin_name,
            "role": "admin",
            "tenant_id": tenant_id
        }
    }

@router.post("/login")
async def login_simple(data: LoginRequest):
    """Simple login for demo purposes"""
    
    user = demo_users.get(data.email)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = f"token_{secrets.token_urlsafe(32)}"
    
    return {
        "access_token": access_token,
        "refresh_token": f"refresh_{secrets.token_urlsafe(32)}",
        "token_type": "bearer",
        "expires_in": 1800,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "tenant_id": user["tenant_id"]
        }
    }

@router.get("/me")
async def get_current_user():
    """Get current user info"""
    return {
        "id": "demo_user",
        "email": "demo@nexus.com",
        "full_name": "Demo User",
        "role": "admin",
        "tenant_id": "demo_tenant"
    }