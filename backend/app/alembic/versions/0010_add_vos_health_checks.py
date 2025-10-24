"""add vos health checks table

Revision ID: 0010
Revises: 0009
Create Date: 2025-10-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'vos_health_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_instance_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('last_check_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('api_success', sa.Boolean(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vos_instance_id'], ['vos_instances.id'], ),
    )
    op.create_index(op.f('ix_vos_health_checks_id'), 'vos_health_checks', ['id'], unique=False)
    op.create_index(op.f('ix_vos_health_checks_vos_instance_id'), 'vos_health_checks', ['vos_instance_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_vos_health_checks_vos_instance_id'), table_name='vos_health_checks')
    op.drop_index(op.f('ix_vos_health_checks_id'), table_name='vos_health_checks')
    op.drop_table('vos_health_checks')

