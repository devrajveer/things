from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from yp_api.domain.uow import UnitOfWork
from yp_api.infrastructure.persistence.users_repo import SQLAlchemyUserRepository

class SQLAlchemyOrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, org):
        from yp_api.models.auth import Organization
        result = await self.session.execute(select(Organization).where(Organization.id == org.id))
        model = result.scalar_one_or_none()
        if not model:
            model = Organization(**org.model_dump(exclude_none=True))
            self.session.add(model)
        else:
            for k, v in org.model_dump(exclude_none=True).items():
                setattr(model, k, v)
        await self.session.flush()
        return org

    async def save_member(self, member):
        from yp_api.models.auth import OrganizationMember
        result = await self.session.execute(
            select(OrganizationMember).where(
                OrganizationMember.org_id == member.org_id,
                OrganizationMember.user_id == member.user_id
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            model = OrganizationMember(**member.model_dump(exclude_none=True))
            self.session.add(model)
        else:
            for k, v in member.model_dump(exclude_none=True).items():
                setattr(model, k, v)
        await self.session.flush()
        return member

    async def get_by_id(self, id: str):
        from yp_api.models.auth import Organization
        from yp_api.domain.organizations.entities import Organization as OrganizationEntity
        result = await self.session.execute(select(Organization).where(Organization.id == id))
        model = result.scalar_one_or_none()
        if model:
            return OrganizationEntity.model_validate(model)
        return None

    async def list_for_user(self, user_id: str):
        from yp_api.models.auth import Organization, OrganizationMember
        from yp_api.domain.organizations.entities import Organization as OrganizationEntity
        result = await self.session.execute(
            select(Organization)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
        )
        models = result.scalars().all()
        return [OrganizationEntity.model_validate(m) for m in models]

    async def get_member(self, org_id: str, user_id: str):
        from yp_api.models.auth import OrganizationMember
        from yp_api.domain.organizations.entities import OrganizationMember as OrganizationMemberEntity
        result = await self.session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.org_id == org_id, OrganizationMember.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return OrganizationMemberEntity.model_validate(model)
        return None

    async def delete(self, id: str):
        from yp_api.models.auth import Organization
        from sqlalchemy import delete as sql_delete
        await self.session.execute(sql_delete(Organization).where(Organization.id == id))
        await self.session.flush()

    async def list_members(self, org_id: str):
        from yp_api.models.auth import OrganizationMember, User
        from yp_api.domain.organizations.entities import OrganizationMember as OrganizationMemberEntity
        result = await self.session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.org_id == org_id)
        )
        models = result.scalars().all()
        return [OrganizationMemberEntity.model_validate(m) for m in models]

    async def count_members(self, org_id: str) -> int:
        from yp_api.models.auth import OrganizationMember
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(OrganizationMember.user_id))
            .where(OrganizationMember.org_id == org_id)
        )
        return result.scalar() or 0

    async def count_owners(self, org_id: str):
        from yp_api.models.auth import OrganizationMember
        from sqlalchemy import select, func
        result = await self.session.execute(
            select(func.count(OrganizationMember.user_id))
            .where(OrganizationMember.org_id == org_id, OrganizationMember.role == "owner")
        )
        return result.scalar() or 0

    async def delete_member(self, org_id: str, user_id: str):
        from yp_api.models.auth import OrganizationMember
        from sqlalchemy import delete as sql_delete
        await self.session.execute(
            sql_delete(OrganizationMember)
            .where(OrganizationMember.org_id == org_id, OrganizationMember.user_id == user_id)
        )
        await self.session.flush()

class SQLAlchemyProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, project):
        from yp_api.models.core import Project
        result = await self.session.execute(select(Project).where(Project.id == project.id))
        model = result.scalar_one_or_none()
        if not model:
            model = Project(**project.model_dump(exclude_none=True))
            self.session.add(model)
        else:
            for k, v in project.model_dump(exclude_none=True).items():
                setattr(model, k, v)
        await self.session.flush()
        return project

    async def get(self, id: str):
        from yp_api.models.core import Project
        from yp_api.domain.projects.entities import Project as ProjectEntity
        result = await self.session.execute(
            select(Project).where(Project.id == id, Project.deleted_at == None)
        )
        model = result.scalar_one_or_none()
        if model:
            return ProjectEntity.model_validate(model)
        return None

    async def list_by_org(self, org_id: str):
        from yp_api.models.core import Project
        from yp_api.domain.projects.entities import Project as ProjectEntity
        result = await self.session.execute(
            select(Project)
            .where(Project.org_id == org_id, Project.deleted_at == None)
            .order_by(Project.created_at.desc())
        )
        models = result.scalars().all()
        return [ProjectEntity.model_validate(m) for m in models]

    async def list_by_user(self, user_id: str):
        from yp_api.models.core import Project, ProjectMember
        from yp_api.domain.projects.entities import Project as ProjectEntity
        result = await self.session.execute(
            select(Project)
            .join(ProjectMember)
            .where(ProjectMember.user_id == user_id, Project.deleted_at == None)
            .order_by(Project.created_at.desc())
        )
        models = result.scalars().all()
        return [ProjectEntity.model_validate(m) for m in models]

    async def count_by_org(self, org_id: str) -> int:
        from yp_api.models.core import Project
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(Project.id)).where(
                Project.org_id == org_id,
                Project.deleted_at == None
            )
        )
        return result.scalar() or 0

    async def delete(self, id: str):
        from yp_api.models.core import Project
        from datetime import datetime
        from sqlalchemy import update
        await self.session.execute(
            update(Project)
            .where(Project.id == id)
            .values(deleted_at=datetime.utcnow().isoformat())
        )
        await self.session.flush()

    async def check_slug_exists(self, org_id: str, slug: str) -> bool:
        from yp_api.models.core import Project
        from sqlalchemy import select, exists
        result = await self.session.execute(
            select(exists().where(
                Project.org_id == org_id,
                Project.slug == slug,
                Project.deleted_at == None
            ))
        )
        return result.scalar()

class SQLAlchemyProjectMemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, project_id: str, user_id: str):
        from yp_api.models.core import ProjectMember
        from yp_api.domain.projects.entities import ProjectMember as ProjectMemberEntity
        result = await self.session.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return ProjectMemberEntity.model_validate(model)
        return None

    async def save(self, member):
        from yp_api.models.core import ProjectMember
        result = await self.session.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == member.project_id, ProjectMember.user_id == member.user_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            model = ProjectMember(**member.model_dump(exclude_none=True))
            self.session.add(model)
        else:
            for k, v in member.model_dump(exclude_none=True).items():
                setattr(model, k, v)
        await self.session.flush()
        return member

    async def delete(self, project_id: str, user_id: str):
        from yp_api.models.core import ProjectMember
        from sqlalchemy import delete as sql_delete
        await self.session.execute(
            sql_delete(ProjectMember)
            .where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
        await self.session.flush()

    async def list_by_project(self, project_id: str):
        from yp_api.models.core import ProjectMember
        from yp_api.domain.projects.entities import ProjectMember as ProjectMemberEntity
        result = await self.session.execute(
            select(ProjectMember).where(ProjectMember.project_id == project_id)
        )
        models = result.scalars().all()
        return [ProjectMemberEntity.model_validate(m) for m in models]

class SQLAlchemyMagicLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, magic_link):
        from yp_api.models.auth import MagicLink
        result = await self.session.execute(select(MagicLink).where(MagicLink.id == magic_link.id))
        model = result.scalar_one_or_none()
        if not model:
            model = MagicLink(**magic_link.model_dump(exclude_none=True))
            self.session.add(model)
        else:
            for k, v in magic_link.model_dump(exclude_none=True).items():
                setattr(model, k, v)
        await self.session.flush()
        return magic_link

    async def get_by_id(self, id: str):
        from yp_api.models.auth import MagicLink
        from yp_api.domain.users.entities import MagicLink as MagicLinkEntity
        result = await self.session.execute(select(MagicLink).where(MagicLink.id == id))
        model = result.scalar_one_or_none()
        if model:
            return MagicLinkEntity.model_validate(model)
        return None

    async def get_by_hashed_token(self, hashed_token: str):
        from yp_api.models.auth import MagicLink
        from yp_api.domain.users.entities import MagicLink as MagicLinkEntity
        result = await self.session.execute(select(MagicLink).where(MagicLink.hashed_token == hashed_token))
        model = result.scalar_one_or_none()
        if model:
            return MagicLinkEntity.model_validate(model)
        return None

    async def get_latest_for_email(self, email: str, purpose: str):
        from yp_api.models.auth import MagicLink
        from yp_api.domain.users.entities import MagicLink as MagicLinkEntity
        result = await self.session.execute(
            select(MagicLink)
            .where(MagicLink.email == email, MagicLink.purpose == purpose)
            .order_by(MagicLink.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if model:
            return MagicLinkEntity.model_validate(model)
        return None

class SQLAlchemyRefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, refresh_token):
        from yp_api.models.auth import RefreshToken
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.id == refresh_token.id))
        model = result.scalar_one_or_none()
        if not model:
            model = RefreshToken(**refresh_token.model_dump(exclude_none=True))
            self.session.add(model)
        else:
            for k, v in refresh_token.model_dump(exclude_none=True).items():
                setattr(model, k, v)
        await self.session.flush()
        return refresh_token

    async def get_by_id(self, id: str):
        from yp_api.models.auth import RefreshToken
        from yp_api.domain.users.entities import RefreshToken as RefreshTokenEntity
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.id == id))
        model = result.scalar_one_or_none()
        if model:
            return RefreshTokenEntity.model_validate(model)
        return None

    async def get_by_hashed_token(self, hashed_token: str):
        from yp_api.models.auth import RefreshToken
        from yp_api.domain.users.entities import RefreshToken as RefreshTokenEntity
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.hashed_token == hashed_token))
        model = result.scalar_one_or_none()
        if model:
            return RefreshTokenEntity.model_validate(model)
        return None

    async def revoke_all_for_user(self, user_id: str):
        from yp_api.models.auth import RefreshToken
        from sqlalchemy import update
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.used_at == None)
            .values(used_at=datetime.utcnow())
        )
        await self.session.flush()

    async def get_active_by_user(self, user_id: str):
        from yp_api.models.auth import RefreshToken
        from yp_api.domain.users.entities import RefreshToken as RefreshTokenEntity
        from yp_shared.time import utc_now
        result = await self.session.execute(
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.used_at == None,
                RefreshToken.expires_at > utc_now()
            )
            .order_by(RefreshToken.created_at.desc())
        )
        models = result.scalars().all()
        return [RefreshTokenEntity.model_validate(m) for m in models]

    async def get_by_id_and_user(self, id: str, user_id: str):
        from yp_api.models.auth import RefreshToken
        from yp_api.domain.users.entities import RefreshToken as RefreshTokenEntity
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.id == id, RefreshToken.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return RefreshTokenEntity.model_validate(model)
        return None

class SQLAlchemyOrganizationInviteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, invite):
        from yp_api.models.auth import OrganizationInvite
        result = await self.session.execute(select(OrganizationInvite).where(OrganizationInvite.id == invite.id))
        model = result.scalar_one_or_none()
        if not model:
            model = OrganizationInvite(**invite.model_dump(exclude_none=True))
            self.session.add(model)
        else:
            for k, v in invite.model_dump(exclude_none=True).items():
                setattr(model, k, v)
        await self.session.flush()
        return invite

    async def get_by_id(self, id: str):
        from yp_api.models.auth import OrganizationInvite
        from yp_api.domain.organizations.entities import OrganizationInvite as OrganizationInviteEntity
        result = await self.session.execute(select(OrganizationInvite).where(OrganizationInvite.id == id))
        model = result.scalar_one_or_none()
        if model:
            return OrganizationInviteEntity.model_validate(model)
        return None

    async def get_by_hashed_token(self, hashed_token: str):
        from yp_api.models.auth import OrganizationInvite
        from yp_api.domain.organizations.entities import OrganizationInvite as OrganizationInviteEntity
        result = await self.session.execute(select(OrganizationInvite).where(OrganizationInvite.hashed_token == hashed_token))
        model = result.scalar_one_or_none()
        if model:
            return OrganizationInviteEntity.model_validate(model)
        return None

    async def list_by_org(self, org_id: str):
        from yp_api.models.auth import OrganizationInvite
        from yp_api.domain.organizations.entities import OrganizationInvite as OrganizationInviteEntity
        result = await self.session.execute(select(OrganizationInvite).where(OrganizationInvite.org_id == org_id))
        models = result.scalars().all()
        return [OrganizationInviteEntity.model_validate(m) for m in models]

    async def delete(self, id: str):
        from yp_api.models.auth import OrganizationInvite
        from sqlalchemy import delete as sql_delete
        await self.session.execute(sql_delete(OrganizationInvite).where(OrganizationInvite.id == id))
        await self.session.flush()

class SQLAlchemyAuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event):
        from yp_api.models.core import AuditEvent
        model = AuditEvent(**event.model_dump(exclude_none=True))
        self.session.add(model)
        await self.session.flush()
        return event

class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: AsyncSession = None
        self.users = None
        self.organizations = None
        self.projects = None
        self.project_members = None
        self.magic_links = None
        self.refresh_tokens = None
        self.organization_invites = None
        self.audit_events = None
        self.devices = None
        self.device_profiles = None
        self.streams = None
        self.dashboards = None

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self.session = self.session_factory()
        self.users = SQLAlchemyUserRepository(self.session)
        self.organizations = SQLAlchemyOrganizationRepository(self.session)
        self.projects = SQLAlchemyProjectRepository(self.session)
        self.project_members = SQLAlchemyProjectMemberRepository(self.session)
        self.magic_links = SQLAlchemyMagicLinkRepository(self.session)
        self.refresh_tokens = SQLAlchemyRefreshTokenRepository(self.session)
        self.organization_invites = SQLAlchemyOrganizationInviteRepository(self.session)
        self.audit_events = SQLAlchemyAuditRepository(self.session)
        
        from yp_api.infrastructure.persistence.sql_devices import (
            SQLDeviceRepository,
            SQLDeviceProfileRepository,
            SQLStreamRepository
        )
        from yp_api.infrastructure.persistence.sql_dashboards import SQLDashboardRepository
        from yp_api.infrastructure.persistence.sql_automation import SQLRuleRepository, SQLWebhookRepository
        from yp_api.infrastructure.persistence.sql_fleets import SQLFleetRepository, SQLFirmwareRepository
        self.devices = SQLDeviceRepository(self.session)
        self.device_profiles = SQLDeviceProfileRepository(self.session)
        self.streams = SQLStreamRepository(self.session)
        self.dashboards = SQLDashboardRepository(self.session)
        self.rules = SQLRuleRepository(self.session)
        self.webhooks = SQLWebhookRepository(self.session)
        self.fleets = SQLFleetRepository(self.session)
        self.firmwares = SQLFirmwareRepository(self.session)
        
        return self


    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        if exc_type is not None:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
