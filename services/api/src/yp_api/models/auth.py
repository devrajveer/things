from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import CITEXT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from yp_api.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    org_memberships: Mapped[list["OrganizationMember"]] = relationship(back_populates="user")
    project_memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    hashed_token: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), index=True, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

class MagicLink(Base):
    __tablename__ = "magic_links"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    hashed_token: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), index=True, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False)

    members: Mapped[list["OrganizationMember"]] = relationship(back_populates="organization")

class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="org_memberships")

class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    hashed_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

class OrganizationInvite(Base, TimestampMixin):
    __tablename__ = "organization_invites"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    email: Mapped[str] = mapped_column(CITEXT, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    hashed_token: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), index=True, nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship()

class DeviceCredentials(Base):
    __tablename__ = "device_credentials"

    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
    mqtt_username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    mqtt_password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    http_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    rotated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

