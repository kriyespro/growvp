from django.db import models
from booking.models import Appointment
from users.models import Business

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid')
    ]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='invoices')
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='invoice')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="e.g. GST")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Invoice {self.id} for {self.appointment.customer.first_name}"
