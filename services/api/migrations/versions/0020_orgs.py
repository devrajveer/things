"""organizations and projects

Revision ID: 0020
Revises: 0010
Create Date: 2026-04-29 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0020'
down_revision = '0010'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Organizations table
    op.create_table('organizations',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('owner_id', sa.String(length=32), nullable=False),
        sa.Column('tier', sa.String(length=50), server_default='free', nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Organization members
    op.create_table('organization_members',
        sa.Column('org_id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('org_id', 'user_id')
    )

    # 3. Projects table
    op.create_table('projects',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('org_id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('deleted_at', sa.String(length=255), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_org_id'), 'projects', ['org_id'], unique=False)
    op.create_index(op.f('ix_projects_slug'), 'projects', ['slug'], unique=True)

def downgrade() -> None:
    op.drop_table('projects')
    op.drop_table('organization_members')
    op.drop_table('organizations')
