import sys
import os

# Add the parent directory to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.clickhouse_db import get_clickhouse_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_clickhouse_schema():
    try:
        logger.info("Starting to fix ClickHouse schema...")
        ch_db = get_clickhouse_db()
        
        # Check if column exists
        check_sql = "SELECT name FROM system.columns WHERE database = 'vos_cdrs' AND table = 'cdrs' AND name = 'caller_gateway'"
        result = ch_db.execute(check_sql)
        
        if not result:
            logger.info("Column 'caller_gateway' is missing. Adding it now...")
            # Add column
            add_column_sql = "ALTER TABLE cdrs ADD COLUMN IF NOT EXISTS caller_gateway String COMMENT '对接网关（主叫网关）'"
            ch_db.execute(add_column_sql)
            logger.info("✅ Successfully added column 'caller_gateway'.")
            
            # Add index
            add_index_sql = "ALTER TABLE cdrs ADD INDEX IF NOT EXISTS idx_caller_gateway caller_gateway TYPE minmax GRANULARITY 4"
            ch_db.execute(add_index_sql)
            logger.info("✅ Successfully added index for 'caller_gateway'.")
        else:
            logger.info("Column 'caller_gateway' already exists.")
            
        # Verify
        result = ch_db.execute(check_sql)
        if result:
            logger.info("✅ Verification successful: Column 'caller_gateway' exists.")
        else:
            logger.error("❌ Verification failed: Column 'caller_gateway' still missing.")

    except Exception as e:
        logger.error(f"❌ Failed to fix ClickHouse schema: {e}")

if __name__ == "__main__":
    fix_clickhouse_schema()
