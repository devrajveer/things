"""project description

Revision ID: 0022
Revises: 0021
Create Date: 2026-05-05 13:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('projects', sa.Column('description', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('projects', 'description')
