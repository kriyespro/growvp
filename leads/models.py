from django.conf import settings
from django.db import models

from users.models import Business


class Enquiry(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("replied", "Replied"),
        ("closed", "Closed"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="enquiries"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enquiries",
    )
    subject = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Enquiry #{self.pk} → {self.business.name}"


class EnquiryMessage(models.Model):
    enquiry = models.ForeignKey(
        Enquiry, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enquiry_messages",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message #{self.pk} on enquiry {self.enquiry_id}"
