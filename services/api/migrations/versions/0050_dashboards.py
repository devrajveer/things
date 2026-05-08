"""dashboards table

Revision ID: 0050
Revises: 0040
Create Date: 2026-05-05 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0050'
down_revision = '0040'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'dashboards',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('layout', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboards_project_id'), 'dashboards', ['project_id'], unique=False)

def downgrade() -> None:
    op.drop_table('dashboards')
