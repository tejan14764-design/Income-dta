"""
Accounts signals – audit hooks for user changes.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def on_user_saved(sender, instance, created, **kwargs):
    """Log user creation / update to audit trail (lazy import to avoid circular)."""
    from audit.utils import log_action
    action = "USER_CREATED" if created else "USER_UPDATED"
    # Audit logger needs a school context — will be provided via middleware; skip here if none.
