import os
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from yp_api.settings import settings
from yp_api.domain.users.entities import User as UserEntity
from yp_api.application.auth.sign_up_user import SignUpUserUseCase
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_api.application.auth.token_service import TokenService
from yp_api.infrastructure.services.fake_email_service import FakeEmailService
from yp_api.infrastructure.services.smtp_email_service import SmtpEmailService
from yp_api.infrastructure.persistence.uow import SQLAlchemyUnitOfWork
from yp_api.domain.uow import UnitOfWork
from yp_api.application.auth.login_user import LoginUserUseCase
from yp_api.application.auth.rotate_tokens import RotateTokensUseCase
from yp_api.application.auth.logout_user import LogoutUserUseCase
from yp_api.application.auth.request_password_reset import RequestPasswordResetUseCase
from yp_api.application.auth.reset_password import ResetPasswordUseCase
from yp_api.application.auth.request_magic_link import RequestMagicLinkUseCase
from yp_api.application.auth.verify_magic_link import VerifyMagicLinkUseCase
from yp_api.application.auth.list_sessions import ListUserSessionsUseCase
from yp_api.application.auth.revoke_session import RevokeSessionUseCase
from yp_api.application.auth.rate_limiter import LoginRateLimiter
from yp_api.domain.auth.policy import PolicyEngine, ProjectPermission, ProjectContext
from yp_api.application.organizations.quota_service import QuotaService

# Using a global fake for tests
_fake_email_service = FakeEmailService()

def get_email_service():
    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        return SmtpEmailService(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            from_email=settings.SMTP_FROM or "noreply@megaiot.com"
        )
    return _fake_email_service

def get_sign_up_use_case(request: Request) -> SignUpUserUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    token_service = TokenService()
    return SignUpUserUseCase(uow, password_hasher, token_service, get_email_service())

def get_login_use_case(request: Request) -> LoginUserUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
        
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    token_service = TokenService()
    
    # Get Redis from app state
    redis_client = getattr(request.app.state, "redis", None)
    rate_limiter = LoginRateLimiter(redis_client)
    
    return LoginUserUseCase(uow, password_hasher, token_service, rate_limiter)

def get_rotate_tokens_use_case(request: Request) -> RotateTokensUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
        
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    token_service = TokenService()
    
    return RotateTokensUseCase(uow, password_hasher, token_service)

def get_logout_use_case(request: Request) -> LogoutUserUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
        
    uow = SQLAlchemyUnitOfWork(session_maker)
    return LogoutUserUseCase(uow)

def get_request_password_reset_use_case(request: Request) -> RequestPasswordResetUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
        
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    email_service = _fake_email_service
    
    return RequestPasswordResetUseCase(uow, password_hasher, email_service)

def get_reset_password_use_case(request: Request) -> ResetPasswordUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
        
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    email_service = _fake_email_service
    
    return ResetPasswordUseCase(uow, password_hasher, email_service)

def get_request_magic_link_use_case(request: Request) -> RequestMagicLinkUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
        
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    email_service = _fake_email_service
    
    return RequestMagicLinkUseCase(uow, password_hasher, email_service)

def get_verify_magic_link_use_case(request: Request) -> VerifyMagicLinkUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
        
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    token_service = TokenService()
    
    return VerifyMagicLinkUseCase(uow, password_hasher, token_service)

security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token_service = TokenService()
    payload = token_service.decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "unauthorized", "message": "Invalid or expired token"}}
        )
    return payload["sub"]

async def get_current_user(
    request: Request,
    user_id: str = Depends(get_current_user_id)
) -> UserEntity:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
    uow = SQLAlchemyUnitOfWork(session_maker)
    
    async with uow:
        user = await uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "unauthorized", "message": "User not found"}}
            )
        
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "forbidden", "message": "User account is not active"}}
            )
        
        return user

def get_list_sessions_use_case(request: Request) -> ListUserSessionsUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
    uow = SQLAlchemyUnitOfWork(session_maker)
    return ListUserSessionsUseCase(uow)

def get_revoke_session_use_case(request: Request) -> RevokeSessionUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if not session_maker:
        session_maker = lambda: None
    uow = SQLAlchemyUnitOfWork(session_maker)
    return RevokeSessionUseCase(uow)

from yp_api.application.organizations.get_org import GetOrganizationUseCase
from yp_api.application.organizations.list_orgs import ListOrganizationsUseCase
from yp_api.application.organizations.create_org import CreateOrganizationUseCase
from yp_api.application.organizations.update_org import UpdateOrganizationUseCase
from yp_api.application.organizations.delete_org import DeleteOrganizationUseCase

def get_org_use_case(request: Request) -> GetOrganizationUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return GetOrganizationUseCase(uow)

def get_list_orgs_use_case(request: Request) -> ListOrganizationsUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return ListOrganizationsUseCase(uow)

def get_create_org_use_case(request: Request) -> CreateOrganizationUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return CreateOrganizationUseCase(uow)

def get_update_org_use_case(request: Request) -> UpdateOrganizationUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return UpdateOrganizationUseCase(uow)

def get_delete_org_use_case(request: Request) -> DeleteOrganizationUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return DeleteOrganizationUseCase(uow)

from yp_api.application.organizations.invite_member import InviteMemberUseCase
from yp_api.application.organizations.accept_invite import AcceptInviteUseCase
from yp_api.application.organizations.update_member import UpdateMemberUseCase
from yp_api.application.organizations.remove_member import RemoveMemberUseCase
from yp_api.application.organizations.list_members import ListMembersUseCase
from yp_api.application.organizations.list_invites import ListInvitesUseCase

def get_invite_member_use_case(request: Request) -> InviteMemberUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return InviteMemberUseCase(uow)

def get_accept_invite_use_case(request: Request) -> AcceptInviteUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return AcceptInviteUseCase(uow)

def get_update_member_use_case(request: Request) -> UpdateMemberUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return UpdateMemberUseCase(uow)

def get_remove_member_use_case(request: Request) -> RemoveMemberUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return RemoveMemberUseCase(uow)

def get_list_members_use_case(request: Request) -> ListMembersUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return ListMembersUseCase(uow)

def get_list_invites_use_case(request: Request) -> ListInvitesUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return ListInvitesUseCase(uow)

from yp_api.application.projects.create_project import CreateProjectUseCase
from yp_api.application.projects.get_project import GetProjectUseCase
from yp_api.application.projects.list_projects import ListProjectsUseCase
from yp_api.application.projects.update_project import UpdateProjectUseCase
from yp_api.application.projects.delete_project import DeleteProjectUseCase

def get_create_project_use_case(request: Request) -> CreateProjectUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    quota_service = get_quota_service(request)
    return CreateProjectUseCase(uow, quota_service)

def get_get_project_use_case(request: Request) -> GetProjectUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return GetProjectUseCase(uow)

def get_list_projects_use_case(request: Request) -> ListProjectsUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return ListProjectsUseCase(uow)

def get_update_project_use_case(request: Request) -> UpdateProjectUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return UpdateProjectUseCase(uow)

def get_delete_project_use_case(request: Request) -> DeleteProjectUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    return DeleteProjectUseCase(uow)

def get_uow(request: Request) -> UnitOfWork:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    return SQLAlchemyUnitOfWork(session_maker)

async def get_project_context(
    project_id: str,
    current_user: UserEntity = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
) -> ProjectContext:
    async with uow:
        # 1. Get Project to find its Org
        project = await uow.projects.get(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "not_found", "message": "Project not found"}}
            )
        
        # 2. Get User's role in that Org
        org_member = await uow.organizations.get_member(project.org_id, current_user.id)
        org_role = org_member.role if org_member else None
        
        # 3. Get User's role in that Project
        project_member = await uow.project_members.get(project_id, current_user.id)
        project_role = project_member.role if project_member else None
        
        return ProjectContext(org_role=org_role, project_role=project_role)

def require_project_permission(permission: ProjectPermission):
    async def dependency(
        context: ProjectContext = Depends(get_project_context)
    ):
        if not PolicyEngine.can(permission, context):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "forbidden", "message": f"Action '{permission.value}' is forbidden for your current role"}}
            )
    return dependency

def get_quota_service(request: Request) -> QuotaService:
    uow = get_uow(request)
    redis_client = getattr(request.app.state, "redis", None)
    return QuotaService(uow, redis_client)

async def get_db_session(request: Request):
    session_maker = getattr(request.app.state, "db_session_maker", None)
    if session_maker:
        async with session_maker() as session:
            yield session
    else:
        yield None
