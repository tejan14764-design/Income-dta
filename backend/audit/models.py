"""
INCOME – Audit log model.
Immutable records of significant actions.
"""

import uuid
from django.db import models


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_logs"
    )
    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=100)   # e.g. "PAYMENT_VERIFIED"
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=500, blank=True)
    previous_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    extra = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["school", "action", "timestamp"]),
            models.Index(fields=["actor", "timestamp"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "system"
        return f"[{self.timestamp}] {actor_name}: {self.action} on {self.object_repr}"
