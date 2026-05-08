"""fleets and firmwares

Revision ID: 0070
Revises: 0060
Create Date: 2026-05-06 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0070'
down_revision = '0060'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Firmwares table
    op.create_table(
        'firmwares',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('checksum', sa.String(length=255), nullable=True),
        sa.Column('release_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_firmwares_project_id'), 'firmwares', ['project_id'], unique=False)

    # 2. Fleets table
    op.create_table(
        'fleets',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_firmware_id', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_firmware_id'], ['firmwares.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fleets_project_id'), 'fleets', ['project_id'], unique=False)
    op.create_index(op.f('ix_fleets_target_firmware_id'), 'fleets', ['target_firmware_id'], unique=False)

    # 3. Modify devices table
    op.add_column('devices', sa.Column('fleet_id', sa.String(length=32), nullable=True))
    op.add_column('devices', sa.Column('current_firmware_version', sa.String(length=100), nullable=True))
    op.create_foreign_key('fk_devices_fleet_id', 'devices', 'fleets', ['fleet_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_devices_fleet_id'), 'devices', ['fleet_id'], unique=False)

def downgrade() -> None:
    op.drop_constraint('fk_devices_fleet_id', 'devices', type_='foreignkey')
    op.drop_index(op.f('ix_devices_fleet_id'), table_name='devices')
    op.drop_column('devices', 'current_firmware_version')
    op.drop_column('devices', 'fleet_id')
    op.drop_table('fleets')
    op.drop_table('firmwares')
