from django.db import models
from users.models import Business

class Customer(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='customers')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['business', 'phone']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"
