"""users and sessions

Revision ID: 0010
Revises: 
Create Date: 2026-04-23 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0010'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext"')

    # 2. Users table
    op.create_table('users',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('email', postgresql.CITEXT(), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email_verified_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=False),
        sa.Column('locale', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('failed_login_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('locked_until', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 3. Refresh tokens
    op.create_table('refresh_tokens',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('hashed_token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('used_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_expires_at'), 'refresh_tokens', ['expires_at'], unique=False)

    # 4. Magic links
    op.create_table('magic_links',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('email', postgresql.CITEXT(), nullable=False),
        sa.Column('hashed_token', sa.String(length=255), nullable=False),
        sa.Column('purpose', sa.String(length=50), nullable=False),
        sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('used_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_magic_links_email'), 'magic_links', ['email'], unique=False)
    op.create_index(op.f('ix_magic_links_expires_at'), 'magic_links', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_table('magic_links')
    op.drop_table('refresh_tokens')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
