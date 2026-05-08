"""telemetry hypertable

Revision ID: 0040
Revises: 0030
Create Date: 2026-05-05 18:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0040'
down_revision = '0030'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create telemetry table
    op.create_table(
        'telemetry',
        sa.Column('time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('project_id', sa.String(length=32), nullable=False),
        sa.Column('device_id', sa.String(length=32), nullable=False),
        sa.Column('stream_id', sa.String(length=32), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('value_num', sa.Float(), nullable=True),
        sa.Column('value_bool', sa.Boolean(), nullable=True),
        sa.Column('value_str', sa.Text(), nullable=True),
        sa.Column('value_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('ingested_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. Create hypertable
    # Note: We use execute since create_hypertable is a TimescaleDB function
    op.execute("SELECT create_hypertable('telemetry', 'time', chunk_time_interval => interval '1 day')")

    # 3. Create indexes
    op.create_index('ix_telemetry_project_time', 'telemetry', ['project_id', 'time'], unique=False)
    op.create_index('ix_telemetry_stream_time', 'telemetry', ['stream_id', 'time'], unique=False)
    op.create_index('ix_telemetry_device_key_time', 'telemetry', ['device_id', 'key', 'time'], unique=False)

    # 4. Compression policy (7 days)
    op.execute("ALTER TABLE telemetry SET (timescaledb.compress, timescaledb.compress_segmentby = 'project_id, device_id, key')")
    op.execute("SELECT add_compression_policy('telemetry', interval '7 days')")

    # 5. Retention policy (365 days)
    op.execute("SELECT add_retention_policy('telemetry', interval '365 days')")

def downgrade() -> None:
    op.drop_table('telemetry')
