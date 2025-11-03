"""add vos_uuid fields to all tables

Revision ID: 0011_add_vos_uuid_fields
Revises: 0010_add_vos_health_checks
Create Date: 2025-10-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '0011_add_vos_uuid_fields'
down_revision = '0010_add_vos_health_checks'
branch_labels = None
depends_on = None


def upgrade():
    """为所有相关表添加vos_uuid字段"""
    
    # 1. 为vos_instances表添加vos_uuid字段
    # 检查字段是否已存在
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('vos_instances')]
    
    if 'vos_uuid' not in columns:
        op.add_column('vos_instances', sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=True))
        
        # 为现有记录生成UUID（如果有数据）
        op.execute("""
            UPDATE vos_instances 
            SET vos_uuid = gen_random_uuid() 
            WHERE vos_uuid IS NULL
        """)
        
        # 设置NOT NULL并添加唯一约束
        op.alter_column('vos_instances', 'vos_uuid', nullable=False)
        
        # 添加唯一约束
        try:
            op.create_unique_constraint('uq_vos_instances_uuid', 'vos_instances', ['vos_uuid'])
        except Exception:
            pass  # 如果已存在则跳过
        
        # 添加索引
        try:
            op.create_index('idx_vos_instances_uuid', 'vos_instances', ['vos_uuid'], unique=False)
        except Exception:
            pass  # 如果已存在则跳过
    
    # 2. 为phones表添加vos_uuid字段
    op.add_column('phones', sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    
    # 为现有记录填充vos_uuid
    op.execute("""
        UPDATE phones 
        SET vos_uuid = vi.vos_uuid 
        FROM vos_instances vi 
        WHERE phones.vos_id = vi.id 
        AND phones.vos_uuid IS NULL
    """)
    
    # 添加索引
    op.create_index('idx_phones_vos_uuid', 'phones', ['vos_uuid'], unique=False)
    
    # 3. 为customers表添加vos_uuid字段（如果表存在）
    try:
        op.add_column('customers', sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=True))
        
        # 为现有记录填充vos_uuid
        op.execute("""
            UPDATE customers 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE customers.vos_instance_id = vi.id 
            AND customers.vos_uuid IS NULL
        """)
        
        # 添加索引
        op.create_index('idx_customers_vos_uuid', 'customers', ['vos_uuid'], unique=False)
    except:
        pass  # 如果表不存在则跳过
    
    # 4. 为gateways表添加vos_uuid字段（如果表存在）
    try:
        op.add_column('gateways', sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=True))
        
        # 为现有记录填充vos_uuid
        op.execute("""
            UPDATE gateways 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE gateways.vos_instance_id = vi.id 
            AND gateways.vos_uuid IS NULL
        """)
        
        # 添加索引
        op.create_index('idx_gateways_vos_uuid', 'gateways', ['vos_uuid'], unique=False)
    except:
        pass  # 如果表不存在则跳过
    
    # 5. 为vos_data_cache表添加vos_uuid字段（如果表存在）
    try:
        op.add_column('vos_data_cache', sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=True))
        
        # 为现有记录填充vos_uuid
        op.execute("""
            UPDATE vos_data_cache 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE vos_data_cache.vos_instance_id = vi.id 
            AND vos_data_cache.vos_uuid IS NULL
        """)
        
        # 添加索引
        op.create_index('idx_vos_data_cache_vos_uuid', 'vos_data_cache', ['vos_uuid'], unique=False)
    except:
        pass  # 如果表不存在则跳过
    
    # 6. 为vos_health_checks表添加vos_uuid字段（如果表存在）
    try:
        op.add_column('vos_health_checks', sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=True))
        
        # 为现有记录填充vos_uuid
        op.execute("""
            UPDATE vos_health_checks 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE vos_health_checks.vos_instance_id = vi.id 
            AND vos_health_checks.vos_uuid IS NULL
        """)
        
        # 添加索引
        op.create_index('idx_vos_health_checks_vos_uuid', 'vos_health_checks', ['vos_uuid'], unique=False)
    except:
        pass  # 如果表不存在则跳过
    
    # 7. 为cdrs表添加vos_uuid字段（如果表存在，PostgreSQL中的cdrs表）
    try:
        op.add_column('cdrs', sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=True))
        
        # 为现有记录填充vos_uuid
        op.execute("""
            UPDATE cdrs 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE cdrs.vos_id = vi.id 
            AND cdrs.vos_uuid IS NULL
        """)
        
        # 添加索引
        op.create_index('idx_cdrs_vos_uuid', 'cdrs', ['vos_uuid'], unique=False)
    except:
        pass  # 如果表不存在则跳过


def downgrade():
    """回滚vos_uuid字段"""
    
    # 删除索引和字段（反向操作）
    try:
        op.drop_index('idx_cdrs_vos_uuid', table_name='cdrs')
        op.drop_column('cdrs', 'vos_uuid')
    except:
        pass
    
    try:
        op.drop_index('idx_vos_health_checks_vos_uuid', table_name='vos_health_checks')
        op.drop_column('vos_health_checks', 'vos_uuid')
    except:
        pass
    
    try:
        op.drop_index('idx_vos_data_cache_vos_uuid', table_name='vos_data_cache')
        op.drop_column('vos_data_cache', 'vos_uuid')
    except:
        pass
    
    try:
        op.drop_index('idx_gateways_vos_uuid', table_name='gateways')
        op.drop_column('gateways', 'vos_uuid')
    except:
        pass
    
    try:
        op.drop_index('idx_customers_vos_uuid', table_name='customers')
        op.drop_column('customers', 'vos_uuid')
    except:
        pass
    
    try:
        op.drop_index('idx_phones_vos_uuid', table_name='phones')
        op.drop_column('phones', 'vos_uuid')
    except:
        pass
    
    try:
        op.drop_constraint('uq_vos_instances_uuid', 'vos_instances', type_='unique')
        op.drop_index('idx_vos_instances_uuid', table_name='vos_instances')
        op.drop_column('vos_instances', 'vos_uuid')
    except:
        pass

