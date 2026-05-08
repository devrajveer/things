"""invites and audit

Revision ID: 0021
Revises: 0020
Create Date: 2026-05-05 13:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # organization_invites
    op.create_table(
        'organization_invites',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('org_id', sa.String(length=32), nullable=False),
        sa.Column('email', postgresql.CITEXT(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('hashed_token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('accepted_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_invites_org_id'), 'organization_invites', ['org_id'], unique=False)
    op.create_index(op.f('ix_organization_invites_email'), 'organization_invites', ['email'], unique=False)
    op.create_index(op.f('ix_organization_invites_expires_at'), 'organization_invites', ['expires_at'], unique=False)

    # audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('actor_id', sa.String(length=32), nullable=True),
        sa.Column('target_id', sa.String(length=32), nullable=True),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_action'), 'audit_events', ['action'], unique=False)
    op.create_index(op.f('ix_audit_events_actor_id'), 'audit_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_events_target_id'), 'audit_events', ['target_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_audit_events_target_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_actor_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_action'), table_name='audit_events')
    op.drop_table('audit_events')
    
    op.drop_index(op.f('ix_organization_invites_expires_at'), table_name='organization_invites')
    op.drop_index(op.f('ix_organization_invites_email'), table_name='organization_invites')
    op.drop_index(op.f('ix_organization_invites_org_id'), table_name='organization_invites')
    op.drop_table('organization_invites')
