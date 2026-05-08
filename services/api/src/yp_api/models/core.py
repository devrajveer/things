from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from yp_api.models.base import Base, TimestampMixin

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    deleted_at: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project")

class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="project_memberships")

class DeviceProfile(Base, TimestampMixin):
    __tablename__ = "device_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    decoder_js: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    schema_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    payload_decoder: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(ForeignKey("device_profiles.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    labels: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    last_seen: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    fleet_id: Mapped[Optional[str]] = mapped_column(ForeignKey("fleets.id", ondelete="SET NULL"), index=True, nullable=True)
    current_firmware_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class Stream(Base):
    __tablename__ = "streams"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    last_value_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    first_value_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class Dashboard(Base, TimestampMixin):
    __tablename__ = "dashboards"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    layout: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

class Webhook(Base, TimestampMixin):
    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

class Rule(Base, TimestampMixin):
    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    stream_id: Mapped[Optional[str]] = mapped_column(ForeignKey("streams.id", ondelete="SET NULL"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    condition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    actions: Mapped[list] = mapped_column(JSONB, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

class Firmware(Base, TimestampMixin):
    __tablename__ = "firmwares"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    release_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class Fleet(Base, TimestampMixin):
    __tablename__ = "fleets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_firmware_id: Mapped[Optional[str]] = mapped_column(ForeignKey("firmwares.id", ondelete="SET NULL"), index=True, nullable=True)
