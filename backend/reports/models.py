import uuid
from django.db import models


class ExportLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "schools.School", on_delete=models.SET_NULL, null=True, related_name="export_logs"
    )
    exported_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True
    )
    export_type = models.CharField(max_length=100)
    filters_used = models.JSONField(null=True, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "export_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.export_type} by {self.exported_by} at {self.created_at}"
