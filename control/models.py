from django.conf import settings
from django.db import models


class AdminLog(models.Model):
    """Audit trail for Mission Control staff actions."""

    ACTION_CHOICES = [
        ("ban", "Ban user"),
        ("unban", "Unban user"),
        ("impersonate", "Impersonate user"),
        ("stop_impersonate", "Stop impersonation"),
        ("view", "View profile"),
        ("other", "Other"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="control_actions",
    )
    action = models.CharField(max_length=40, choices=ACTION_CHOICES, default="other")
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="control_events",
    )
    message = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        actor = self.actor.email if self.actor_id else "system"
        return f"{actor}: {self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
