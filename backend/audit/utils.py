"""
INCOME – Audit utility function.
Call log_action() from any service or view to record an audit event.
"""

import logging

logger = logging.getLogger("income.audit")


def log_action(actor, action: str, obj=None, school_id=None, previous=None, new=None, extra=None):
    """
    Records an audit log entry.
    Runs synchronously – consider making async in high-volume scenarios.
    """
    try:
        from .models import AuditLog

        object_type = ""
        object_id = ""
        object_repr = ""

        if obj is not None:
            object_type = type(obj).__name__
            object_id = str(getattr(obj, "pk", "") or "")
            object_repr = str(obj)[:500]

        AuditLog.objects.create(
            school_id=school_id,
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=object_id,
            object_repr=object_repr,
            previous_data=previous,
            new_data=new,
            extra=extra,
        )
    except Exception as e:
        logger.error("Failed to write audit log: %s | action=%s obj=%s", e, action, obj)
