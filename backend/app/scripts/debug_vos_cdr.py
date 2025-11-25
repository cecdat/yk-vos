import sys
import os
import json
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.db import SessionLocal
from app.models.vos_instance import VOSInstance
from app.models.customer import Customer
from app.core.vos_client import VOSClient

def debug_cdr():
    db = SessionLocal()
    try:
        # Get first instance
        inst = db.query(VOSInstance).filter(VOSInstance.enabled == True).first()
        if not inst:
            print("No enabled VOS instance found")
            return

        print(f"Using Instance: {inst.name} ({inst.base_url})")

        # Get a customer
        customer = db.query(Customer).filter(Customer.vos_instance_id == inst.id).first()
        if not customer:
            print("No customer found")
            return

        print(f"Using Customer: {customer.account}")

        client = VOSClient(inst.base_url)
        
        # Query CDRs for the last 3 days
        end_time = datetime.now()
        begin_time = end_time - timedelta(days=3)
        
        payload = {
            'accounts': [customer.account],
            'beginTime': begin_time.strftime('%Y%m%d%H%M%S'),
            'endTime': end_time.strftime('%Y%m%d%H%M%S'),
            'count': 1  # Just get one
        }
        
        print(f"Calling GetCdr with payload: {payload}")
        
        result = client.call_api('/external/server/GetCdr', payload)
        
        if result.get('retCode') != 0:
            print(f"API Error: {result}")
            return

        cdrs = result.get('infoCdrs') or result.get('cdrs') or []
        if not cdrs:
            print("No CDRs found")
            return

        cdr = cdrs[0]
        print("\n=== RAW CDR DATA ===")
        print(json.dumps(cdr, indent=2, ensure_ascii=False))
        
        # Check for potential cost fields
        print("\n=== POTENTIAL COST FIELDS ===")
        potential_fields = ['cost', 'buyingFee', 'supplierFee', 'agentFee', 'profit', 'calleeFee']
        for field in potential_fields:
            if field in cdr:
                print(f"{field}: {cdr[field]}")
            else:
                print(f"{field}: NOT FOUND")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_cdr()
