import sys
import os

# Add the parent directory to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.db import SessionLocal
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_customer_stats_view():
    db = SessionLocal()
    try:
        logger.info("Starting to update vw_customer_statistics view...")
        
        # SQL to recreate the view without the 'WHERE vi.enabled = TRUE' clause
        sql = """
        CREATE OR REPLACE VIEW vw_customer_statistics AS
        SELECT 
            vi.id AS instance_id,
            vi.name AS instance_name,
            vi.vos_uuid,
            vi.enabled AS instance_enabled,
            COUNT(c.id) AS total_customers,
            COUNT(CASE WHEN c.is_in_debt = TRUE THEN 1 END) AS debt_customers,
            COALESCE(SUM(CASE WHEN c.is_in_debt = TRUE THEN 1 ELSE 0 END), 0) AS debt_count
        FROM vos_instances vi
        LEFT JOIN customers c ON c.vos_instance_id = vi.id
        -- WHERE clause removed to include disabled instances
        GROUP BY vi.id, vi.name, vi.vos_uuid, vi.enabled;
        """
        
        db.execute(text(sql))
        db.commit()
        
        logger.info("✅ Successfully updated vw_customer_statistics view.")
        
        # Also refresh the materialized view if it exists
        try:
            logger.info("Refreshing materialized view mv_dashboard_statistics...")
            db.execute(text("REFRESH MATERIALIZED VIEW mv_dashboard_statistics"))
            db.commit()
            logger.info("✅ Successfully refreshed mv_dashboard_statistics.")
        except Exception as e:
            logger.warning(f"Could not refresh materialized view (might not exist yet): {e}")

    except Exception as e:
        logger.error(f"❌ Failed to update view: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_customer_stats_view()
