import sys
import os
from clickhouse_driver import Client

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings

def upgrade_schema():
    print(f"Connecting to ClickHouse at {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}...")
    
    try:
        client = Client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DB
        )
        
        # New columns to add
        # (name, type, comment)
        new_columns = [
            ('fee_prefix', 'String', '计费前缀'),
            ('call_level', 'UInt8', '通话级别(1:网内 2:市话 4:国内 5:国际)'),
            ('agent_fee', 'Decimal(10, 4)', '代理商费用'),
            ('agent_account', 'String', '代理商账户'),
            ('suite_fee', 'Decimal(10, 4)', '套餐费用')
        ]
        
        # Check existing columns
        existing_columns = client.execute("DESCRIBE TABLE cdrs")
        existing_col_names = [col[0] for col in existing_columns]
        
        for col_name, col_type, col_comment in new_columns:
            if col_name not in existing_col_names:
                print(f"Adding column: {col_name} ({col_type})...")
                sql = f"ALTER TABLE cdrs ADD COLUMN IF NOT EXISTS {col_name} {col_type} COMMENT '{col_comment}'"
                client.execute(sql)
                print(f"✅ Added {col_name}")
            else:
                print(f"ℹ️ Column {col_name} already exists")
                
        print("\n✅ Schema upgrade completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error upgrading schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    upgrade_schema()
