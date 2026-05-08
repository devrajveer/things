"""devices and streams

Revision ID: 0030
Revises: 0022
Create Date: 2026-05-05 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0030'
down_revision = '0022'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Device Profiles
    op.create_table(
        'device_profiles',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('schema_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('payload_decoder', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('decoder_js', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_device_profiles_project_name')
    )
    op.create_index(op.f('ix_device_profiles_project_id'), 'device_profiles', ['project_id'], unique=False)

    # Note: Built-in profiles are usually seeded per project on creation or globally.
    # Here we skip global seeding because they must belong to a project_id.
    # However, we can create a "System" project or just let users create them.
    # For now, we follow the spec by adding a note or a function to seed them.

    # Devices
    op.create_table(
        'devices',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('profile_id', sa.String(length=32), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('labels', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='provisioned', nullable=False),
        sa.Column('last_seen_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_id'], ['device_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_devices_project_name')
    )
    op.create_index(op.f('ix_devices_project_id'), 'devices', ['project_id'], unique=False)
    op.create_index('ix_devices_project_status', 'devices', ['project_id', 'status'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))

    # Device Credentials
    op.create_table(
        'device_credentials',
        sa.Column('device_id', sa.String(length=32), nullable=False),
        sa.Column('mqtt_username', sa.String(length=64), nullable=False),
        sa.Column('mqtt_password_hash', sa.String(length=255), nullable=False),
        sa.Column('http_token_hash', sa.String(length=255), nullable=False),
        sa.Column('rotated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('device_id'),
        sa.UniqueConstraint('mqtt_username'),
        sa.UniqueConstraint('http_token_hash')
    )

    # Streams
    op.create_table(
        'streams',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('device_id', sa.String(length=32), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('value_type', sa.String(length=20), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('last_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_value_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('first_value_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id', 'key', name='uq_streams_device_key')
    )
    op.create_index(op.f('ix_streams_project_id'), 'streams', ['project_id'], unique=False)

def downgrade() -> None:
    op.drop_table('streams')
    op.drop_table('device_credentials')
    op.drop_table('devices')
    op.drop_table('device_profiles')
