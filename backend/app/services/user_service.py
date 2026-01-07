import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import secrets
import uuid

from app.models.user import (
    User, Tenant, UserCreate, UserUpdate, TenantCreate, TenantUpdate,
    UserRole, UserStatus, TenantStatus, APIKey, APIKeyCreate,
    UserInvitation, InviteUser, AcceptInvitation, UsageMetrics
)
from app.core.auth import auth_service
from app.db.base import BaseRepository

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_repo: BaseRepository, tenant_repo: BaseRepository, 
                 invitation_repo: BaseRepository, usage_repo: BaseRepository):
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo
        self.invitation_repo = invitation_repo
        self.usage_repo = usage_repo
    
    async def create_tenant_with_admin(self, tenant_data: TenantCreate) -> Dict[str, Any]:
        """Create a new tenant with admin user"""
        try:
            # Create tenant
            tenant = Tenant(
                name=tenant_data.name,
                domain=tenant_data.domain,
                status=TenantStatus.TRIAL,
                plan="beta",
                current_users=1
            )
            
            await self.tenant_repo.create(tenant.model_dump())
            logger.info(f"Created tenant: {tenant.name} ({tenant.id})")
            
            # Create admin user
            admin_user = User(
                email=tenant_data.admin_email,
                full_name=tenant_data.admin_name,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                tenant_id=tenant.id,
                password_hash=auth_service.get_password_hash(tenant_data.admin_password)
            )
            
            await self.user_repo.create(admin_user.model_dump())
            logger.info(f"Created admin user: {admin_user.email} for tenant {tenant.id}")
            
            # Generate simple API key for now
            simple_api_key = f"nexus_{tenant.id}_{secrets.token_urlsafe(16)}"
            
            return {
                "tenant": tenant,
                "admin_user": admin_user,
                "api_key": simple_api_key
            }
            
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tenant"
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            # Query user by email
            users = await self.user_repo.query(
                "SELECT * FROM c WHERE c.email = @email",
                [{"name": "@email", "value": email}]
            )
            
            if not users:
                return None
            
            user_data = users[0]
            user = User(**user_data)
            
            if not auth_service.verify_password(password, user.password_hash):
                return None
            
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is not active"
                )
            
            # Update last login
            await self.user_repo.update(user.id, user.id, {
                "last_login": datetime.utcnow().isoformat()
            })
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            return None
    
    async def create_user(self, user_data: UserCreate, created_by: str) -> User:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_users = await self.user_repo.query(
                "SELECT * FROM c WHERE c.email = @email",
                [{"name": "@email", "value": user_data.email}]
            )
            
            if existing_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Get tenant to check limits
            tenant = await self.get_tenant(user_data.tenant_id)
            if tenant.current_users >= tenant.max_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant has reached maximum user limit"
                )
            
            # Create user
            user = User(
                email=user_data.email,
                full_name=user_data.full_name,
                role=user_data.role,
                tenant_id=user_data.tenant_id,
                password_hash=auth_service.get_password_hash(user_data.password)
            )
            
            await self.user_repo.create(user.model_dump())
            
            # Update tenant user count
            await self.tenant_repo.update(tenant.id, tenant.id, {
                "current_users": tenant.current_users + 1,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Created user: {user.email} for tenant {user.tenant_id}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def invite_user(self, invite_data: InviteUser, tenant_id: str, invited_by: str) -> UserInvitation:
        """Send user invitation"""
        try:
            # Check if user already exists
            existing_users = await self.user_repo.query(
                "SELECT * FROM c WHERE c.email = @email",
                [{"name": "@email", "value": invite_data.email}]
            )
            
            if existing_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Create invitation
            invitation = UserInvitation(
                email=invite_data.email,
                full_name=invite_data.full_name,
                role=invite_data.role,
                tenant_id=tenant_id,
                invited_by=invited_by,
                token=secrets.token_urlsafe(32),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            await self.invitation_repo.create(invitation.model_dump())
            
            # TODO: Send invitation email
            logger.info(f"Created invitation for {invite_data.email} to tenant {tenant_id}")
            
            return invitation
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create invitation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invitation"
            )
    
    async def accept_invitation(self, accept_data: AcceptInvitation) -> User:
        """Accept user invitation and create account"""
        try:
            # Find invitation
            invitations = await self.invitation_repo.query(
                "SELECT * FROM c WHERE c.token = @token AND c.is_accepted = false",
                [{"name": "@token", "value": accept_data.token}]
            )
            
            if not invitations:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired invitation"
                )
            
            invitation_data = invitations[0]
            invitation = UserInvitation(**invitation_data)
            
            if invitation.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation has expired"
                )
            
            # Create user
            user = User(
                email=invitation.email,
                full_name=invitation.full_name,
                role=invitation.role,
                tenant_id=invitation.tenant_id,
                status=UserStatus.ACTIVE,
                password_hash=auth_service.get_password_hash(accept_data.password)
            )
            
            await self.user_repo.create(user.model_dump())
            
            # Mark invitation as accepted
            await self.invitation_repo.update(invitation.id, invitation.id, {
                "is_accepted": True,
                "accepted_at": datetime.utcnow().isoformat()
            })
            
            # Update tenant user count
            tenant = await self.get_tenant(user.tenant_id)
            await self.tenant_repo.update(tenant.id, tenant.id, {
                "current_users": tenant.current_users + 1,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"User {user.email} accepted invitation and joined tenant {user.tenant_id}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to accept invitation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to accept invitation"
            )
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_data = await self.user_repo.get(user_id, partition_key=user_id)
            return User(**user_data) if user_data else None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        try:
            tenant_data = await self.tenant_repo.get(tenant_id, partition_key=tenant_id)
            return Tenant(**tenant_data) if tenant_data else None
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            return None
    
    async def get_tenant_users(self, tenant_id: str) -> List[User]:
        """Get all users for a tenant"""
        try:
            users_data = await self.user_repo.query(
                "SELECT * FROM c WHERE c.tenant_id = @tenant_id",
                [{"name": "@tenant_id", "value": tenant_id}]
            )
            return [User(**user_data) for user_data in users_data]
        except Exception as e:
            logger.error(f"Failed to get users for tenant {tenant_id}: {e}")
            return []
    
    async def create_api_key(self, user_id: str, api_key_data: APIKeyCreate) -> Dict[str, Any]:
        """Create API key for user"""
        try:
            user = await self.get_user(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Generate API key
            key_value = auth_service.generate_api_key(user.id, user.tenant_id)
            
            api_key = APIKey(
                name=api_key_data.name,
                key_hash=auth_service.get_password_hash(key_value),
                user_id=user.id,
                tenant_id=user.tenant_id,
                permissions=api_key_data.permissions,
                expires_at=datetime.utcnow() + timedelta(days=api_key_data.expires_days) if api_key_data.expires_days else None
            )
            
            # Store API key (without the actual key value)
            # Note: API keys should be stored in a separate container, but for now using user_repo
            # In production, create a separate api_keys container
            api_key_dict = api_key.model_dump()
            api_key_dict['id'] = api_key.id  # Ensure ID is set
            await self.user_repo.create(api_key_dict)
            
            # Update user's API key list
            user.api_keys.append(api_key.id)
            await self.user_repo.update(user.id, user.id, {
                "api_keys": user.api_keys,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Created API key {api_key.name} for user {user.email}")
            
            return {
                "id": api_key.id,
                "name": api_key.name,
                "key": key_value,  # Only returned once
                "permissions": api_key.permissions,
                "expires_at": api_key.expires_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
    
    async def track_usage(self, tenant_id: str, metric_type: str, count: int = 1):
        """Track usage metrics for tenant"""
        try:
            today = datetime.utcnow().date()
            usage_id = f"{tenant_id}_{today.isoformat()}"
            
            # Get or create today's usage record
            try:
                usage_data = await self.usage_repo.get(usage_id, partition_key=tenant_id)
                usage = UsageMetrics(**usage_data) if usage_data else None
            except:
                usage = None
            
            if not usage:
                usage = UsageMetrics(
                    tenant_id=tenant_id,
                    period="daily",
                    date=datetime.combine(today, datetime.min.time())
                )
            
            # Update metric
            if metric_type == "incidents_created":
                usage.incidents_created += count
            elif metric_type == "incidents_resolved":
                usage.incidents_resolved += count
            elif metric_type == "ai_analyses":
                usage.ai_analyses_performed += count
            elif metric_type == "notifications":
                usage.notifications_sent += count
            elif metric_type == "api_calls":
                usage.api_calls += count
            
            # Save usage
            await self.usage_repo.upsert(usage.model_dump(), partition_key=tenant_id)
            
        except Exception as e:
            logger.error(f"Failed to track usage for tenant {tenant_id}: {e}")
    
    async def check_tenant_limits(self, tenant_id: str) -> Dict[str, Any]:
        """Check if tenant is within usage limits"""
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                return {"within_limits": False, "error": "Tenant not found"}
            
            # Get current month's usage
            today = datetime.utcnow()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Query usage for current month
            usage_data = await self.usage_repo.query(
                "SELECT * FROM c WHERE c.tenant_id = @tenant_id AND c.date >= @month_start",
                [
                    {"name": "@tenant_id", "value": tenant_id},
                    {"name": "@month_start", "value": month_start.isoformat()}
                ]
            )
            
            total_incidents = sum(usage.get("incidents_created", 0) for usage in usage_data)
            
            within_limits = {
                "users": tenant.current_users <= tenant.max_users,
                "incidents": total_incidents <= tenant.max_incidents_per_month
            }
            
            return {
                "within_limits": all(within_limits.values()),
                "limits": {
                    "max_users": tenant.max_users,
                    "max_incidents_per_month": tenant.max_incidents_per_month
                },
                "current_usage": {
                    "users": tenant.current_users,
                    "incidents_this_month": total_incidents
                },
                "usage_percentage": {
                    "users": (tenant.current_users / tenant.max_users) * 100,
                    "incidents": (total_incidents / tenant.max_incidents_per_month) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to check limits for tenant {tenant_id}: {e}")
            return {"within_limits": False, "error": str(e)}