"""rules and webhooks

Revision ID: 0060
Revises: 0050
Create Date: 2026-05-06 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0060'
down_revision = '0050'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('secret', sa.String(length=255), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhooks_project_id'), 'webhooks', ['project_id'], unique=False)

    # 2. Rules table
    op.create_table(
        'rules',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('stream_id', sa.String(length=32), nullable=True),
        sa.Column('condition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('actions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stream_id'], ['streams.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rules_project_id'), 'rules', ['project_id'], unique=False)
    op.create_index(op.f('ix_rules_stream_id'), 'rules', ['stream_id'], unique=False)

def downgrade() -> None:
    op.drop_table('rules')
    op.drop_table('webhooks')
