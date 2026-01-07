from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer
from datetime import timedelta

from app.models.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin, TokenResponse,
    TenantCreate, TenantResponse, TenantUpdate, InviteUser, AcceptInvitation,
    APIKeyCreate, APIKeyResponse, UserInvitation
)
from app.core.auth import (
    auth_service, get_current_user, get_current_admin, get_current_sre,
    TokenData, UserRole, ACCESS_TOKEN_EXPIRE_MINUTES, rate_limit
)
from app.services.user_service import UserService
from app.api import deps

router = APIRouter()
security = HTTPBearer()

@router.post("/register-tenant", response_model=dict)
async def register_tenant(
    tenant_data: TenantCreate,
    user_service: UserService = Depends(deps.get_user_service)
):
    """Register a new tenant with admin user (for beta onboarding)"""
    result = await user_service.create_tenant_with_admin(tenant_data)
    
    # Create tokens for immediate login
    token_data = {
        "sub": result["admin_user"].id,
        "email": result["admin_user"].email,
        "role": result["admin_user"].role,
        "tenant_id": result["admin_user"].tenant_id
    }
    
    access_token = auth_service.create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth_service.create_refresh_token(data=token_data)
    
    return {
        "message": "Tenant registered successfully",
        "tenant": result["tenant"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "api_key": result["api_key"]
    }

@router.post("/login", response_model=TokenResponse)
@rate_limit(limit=10, window=300)  # 10 attempts per 5 minutes
async def login(
    user_credentials: UserLogin,
    user_service: UserService = Depends(deps.get_user_service)
):
    """Authenticate user and return tokens"""
    user = await user_service.authenticate_user(
        user_credentials.email, 
        user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id
    }
    
    access_token = auth_service.create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth_service.create_refresh_token(data=token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            tenant_id=user.tenant_id,
            last_login=user.last_login,
            created_at=user.created_at,
            preferences=user.preferences
        )
    )

@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_token: str,
    user_service: UserService = Depends(deps.get_user_service)
):
    """Refresh access token using refresh token"""
    try:
        token_data = auth_service.verify_token(refresh_token)
        user = await user_service.get_user(token_data.user_id)
        
        if not user or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        new_token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id
        }
        
        access_token = auth_service.create_access_token(
            data=new_token_data,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Get current user information"""
    user = await user_service.get_user(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        tenant_id=user.tenant_id,
        last_login=user.last_login,
        created_at=user.created_at,
        preferences=user.preferences
    )

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Update current user information"""
    # Users can only update their own profile (except role/status)
    update_data = user_update.dict(exclude_unset=True)
    
    # Remove role and status if not admin
    if current_user.role != UserRole.ADMIN:
        update_data.pop("role", None)
        update_data.pop("status", None)
    
    # Update user
    await user_service.user_repo.update(
        current_user.user_id, 
        current_user.user_id, 
        {**update_data, "updated_at": "datetime.utcnow().isoformat()"}
    )
    
    # Return updated user
    user = await user_service.get_user(current_user.user_id)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        tenant_id=user.tenant_id,
        last_login=user.last_login,
        created_at=user.created_at,
        preferences=user.preferences
    )

# Admin-only endpoints
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: TokenData = Depends(get_current_admin),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Create a new user (admin only)"""
    # Set tenant_id to current user's tenant if not specified
    if not user_data.tenant_id:
        user_data.tenant_id = current_user.tenant_id
    
    # Only allow creating users in same tenant unless super admin
    if user_data.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create users in different tenant"
        )
    
    user = await user_service.create_user(user_data, current_user.user_id)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        tenant_id=user.tenant_id,
        last_login=user.last_login,
        created_at=user.created_at,
        preferences=user.preferences
    )

@router.post("/invite", response_model=dict)
async def invite_user(
    invite_data: InviteUser,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_admin),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Invite a user to join the tenant"""
    invitation = await user_service.invite_user(
        invite_data, 
        current_user.tenant_id, 
        current_user.user_id
    )
    
    # TODO: Send invitation email in background
    # background_tasks.add_task(send_invitation_email, invitation)
    
    return {
        "message": "Invitation sent successfully",
        "invitation_id": invitation.id,
        "expires_at": invitation.expires_at
    }

@router.post("/accept-invitation", response_model=UserResponse)
async def accept_invitation(
    accept_data: AcceptInvitation,
    user_service: UserService = Depends(deps.get_user_service)
):
    """Accept user invitation and create account"""
    user = await user_service.accept_invitation(accept_data)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        tenant_id=user.tenant_id,
        last_login=user.last_login,
        created_at=user.created_at,
        preferences=user.preferences
    )

@router.get("/users", response_model=List[UserResponse])
async def list_tenant_users(
    current_user: TokenData = Depends(get_current_sre),
    user_service: UserService = Depends(deps.get_user_service)
):
    """List all users in current tenant"""
    users = await user_service.get_tenant_users(current_user.tenant_id)
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            tenant_id=user.tenant_id,
            last_login=user.last_login,
            created_at=user.created_at,
            preferences=user.preferences
        )
        for user in users
    ]

@router.get("/tenant", response_model=TenantResponse)
async def get_current_tenant(
    current_user: TokenData = Depends(get_current_user),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Get current tenant information"""
    tenant = await user_service.get_tenant(current_user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status,
        plan=tenant.plan,
        max_users=tenant.max_users,
        max_incidents_per_month=tenant.max_incidents_per_month,
        current_users=tenant.current_users,
        incidents_this_month=tenant.incidents_this_month,
        created_at=tenant.created_at,
        settings=tenant.settings
    )

@router.put("/tenant", response_model=TenantResponse)
async def update_tenant(
    tenant_update: TenantUpdate,
    current_user: TokenData = Depends(get_current_admin),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Update tenant information (admin only)"""
    update_data = tenant_update.dict(exclude_unset=True)
    update_data["updated_at"] = "datetime.utcnow().isoformat()"
    
    await user_service.tenant_repo.update(
        current_user.tenant_id,
        current_user.tenant_id,
        update_data
    )
    
    tenant = await user_service.get_tenant(current_user.tenant_id)
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status,
        plan=tenant.plan,
        max_users=tenant.max_users,
        max_incidents_per_month=tenant.max_incidents_per_month,
        current_users=tenant.current_users,
        incidents_this_month=tenant.incidents_this_month,
        created_at=tenant.created_at,
        settings=tenant.settings
    )

# API Key management
@router.post("/api-keys", response_model=dict)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: TokenData = Depends(get_current_user),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Create API key for current user"""
    api_key = await user_service.create_api_key(current_user.user_id, api_key_data)
    
    return {
        "message": "API key created successfully",
        "api_key": api_key["key"],  # Only shown once
        "id": api_key["id"],
        "name": api_key["name"],
        "permissions": api_key["permissions"],
        "expires_at": api_key["expires_at"]
    }

@router.get("/usage", response_model=dict)
async def get_tenant_usage(
    current_user: TokenData = Depends(get_current_sre),
    user_service: UserService = Depends(deps.get_user_service)
):
    """Get tenant usage and limits"""
    return await user_service.check_tenant_limits(current_user.tenant_id)