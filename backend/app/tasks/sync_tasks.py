from app.tasks.celery_app import celery
from app.core.db import SessionLocal
from app.models.vos_instance import VOSInstance
from app.models.phone import Phone
from app.models.cdr import CDR
from app.core.vos_client import VOSClient
from datetime import datetime, timedelta
import logging, json, hashlib
from dateutil import parser as dateparser
logger = logging.getLogger(__name__)

@celery.task
def sync_all_instances_online_phones():
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        for inst in instances:
            client = VOSClient(inst.base_url)
            res = client.post('/external/server/GetPhoneOnline', payload={})
            phones = res.get('infoPhoneOnlines') or res.get('phones') or []
            if not isinstance(phones, list):
                for v in res.values():
                    if isinstance(v, list):
                        phones = v
                        break
            for p in phones:
                e164 = p.get('e164') or p.get('E164') or p.get('account') or ''
                if not e164:
                    continue
                existing = db.query(Phone).filter(Phone.e164 == e164, Phone.vos_id == inst.id).first()
                if existing:
                    existing.status = 'online'
                else:
                    newp = Phone(e164=e164, status='online', vos_id=inst.id)
                    db.add(newp)
            db.commit()
    except Exception as e:
        logger.exception('Error syncing phones: %s', e)
    finally:
        db.close()

@celery.task
def sync_all_instances_cdrs(days=1):
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        for inst in instances:
            client = VOSClient(inst.base_url)
            end = datetime.utcnow()
            start = end - timedelta(days=days)
            payload = {
                'accounts': [],
                'callerE164': None,
                'calleeE164': None,
                'callerGateway': None,
                'calleeGateway': None,
                'beginTime': start.strftime('%Y%m%d'),
                'endTime': end.strftime('%Y%m%d')
            }
            try:
                res = client.post('/external/server/GetCdr', payload=payload)
            except Exception as e:
                logger.exception('VOS CDR fetch failed for %s: %s', inst.base_url, e)
                continue
            if not isinstance(res, dict):
                logger.warning('Unexpected CDR response type from %s', inst.base_url)
                continue
            if res.get('retCode') != 0:
                logger.warning('VOS returned retCode!=0 for %s: %s', inst.base_url, res.get('exception'))
                continue
            cdrs = res.get('infoCdrs') or res.get('cdrs') or res.get('CDRList') or []
            if not isinstance(cdrs, list):
                for v in res.values():
                    if isinstance(v, list):
                        cdrs = v
                        break
            for c in cdrs:
                caller = c.get('callerE164') or c.get('caller') or c.get('src') or c.get('from') or ''
                callee = c.get('calleeE164') or c.get('callee') or c.get('dst') or c.get('to') or ''
                caller_gw = c.get('callerGateway') or c.get('caller_gateway') or ''
                callee_gw = c.get('calleeGateway') or c.get('callee_gateway') or ''
                start_time = c.get('startTime') or c.get('start_time') or c.get('StartTime') or None
                end_time = c.get('endTime') or c.get('end_time') or c.get('EndTime') or None
                try:
                    if isinstance(start_time, str):
                        parsed = dateparser.parse(start_time)
                        start_time_norm = parsed
                    else:
                        start_time_norm = start_time
                except Exception:
                    start_time_norm = start_time
                duration = c.get('duration') or c.get('billsec') or 0
                cost = c.get('fee') or c.get('cost') or 0
                disposition = c.get('releaseCause') or c.get('disposition') or c.get('status') or ''
                raw = json.dumps(c, ensure_ascii=False)
                h_src = f"{caller}|{callee}|{start_time_norm}|{int(duration)}"
                h = hashlib.sha256(h_src.encode('utf-8')).hexdigest()[:16]
                exists = db.query(CDR).filter(CDR.vos_id==inst.id, CDR.hash==h).first()
                if exists:
                    continue
                newc = CDR(vos_id=inst.id, caller=caller, callee=callee, start_time=start_time_norm, end_time=end_time, duration=duration, cost=cost, disposition=disposition, raw=raw, caller_gateway=caller_gw, callee_gateway=callee_gw, hash=h)
                db.add(newc)
            db.commit()
    except Exception as e:
        logger.exception('Error syncing CDRs: %s', e)
    finally:
        db.close()
