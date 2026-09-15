import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.notification import Notification

logger = logging.getLogger(__name__)

def log_event(db, event, user_id=None, actor_email=None, resource_type=None,
              resource_id=None, description=None, ip_address=None, user_agent=None, metadata=None):
    try:
        entry = AuditLog(
            user_id=str(user_id) if user_id else None,
            event=event,
            actor_email=actor_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            description=description,
            extra_metadata=json.dumps(metadata) if metadata else None
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")
        try: db.rollback()
        except: pass

def send_notification(db, user_id, title, message, type="info", action_url=None, metadata=None):
    try:
        n = Notification(
            user_id=str(user_id),
            title=title, message=message, type=type,
            action_url=action_url,
            extra_metadata=json.dumps(metadata) if metadata else None
        )
        db.add(n)
        db.commit()
    except Exception as e:
        logger.error(f"Notification failed: {e}")
        try: db.rollback()
        except: pass
