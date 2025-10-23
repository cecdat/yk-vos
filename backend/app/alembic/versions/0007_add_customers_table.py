"""add customers table

Revision ID: 0007_add_customers_table
Revises: 0006_optimize_cdr_indexes
Create Date: 2025-10-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007_add_customers_table'
down_revision = '0006_optimize_cdr_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_instance_id', sa.Integer(), nullable=False),
        sa.Column('account', sa.String(length=255), nullable=False),
        sa.Column('money', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('limit_money', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('is_in_debt', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('raw_data', sa.Text(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['vos_instance_id'], ['vos_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)
    op.create_index(op.f('ix_customers_vos_instance_id'), 'customers', ['vos_instance_id'], unique=False)
    op.create_index(op.f('ix_customers_account'), 'customers', ['account'], unique=False)
    op.create_index(op.f('ix_customers_is_in_debt'), 'customers', ['is_in_debt'], unique=False)
    
    # Create composite indexes
    op.create_index('idx_vos_account', 'customers', ['vos_instance_id', 'account'], unique=False)
    op.create_index('idx_vos_debt', 'customers', ['vos_instance_id', 'is_in_debt'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('idx_vos_debt', table_name='customers')
    op.drop_index('idx_vos_account', table_name='customers')
    op.drop_index(op.f('ix_customers_is_in_debt'), table_name='customers')
    op.drop_index(op.f('ix_customers_account'), table_name='customers')
    op.drop_index(op.f('ix_customers_vos_instance_id'), table_name='customers')
    op.drop_index(op.f('ix_customers_id'), table_name='customers')
    
    # Drop table
    op.drop_table('customers')

