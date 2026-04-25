from django.db import models
from users.models import Business, UserProfile
from catalog.models import Service
from crm.models import Customer

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no-show', 'No-Show'),
    ]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='appointments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments')
    provider = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.service.name} for {self.customer.first_name} on {self.date}"
