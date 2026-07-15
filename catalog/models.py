from django.db import models
from users.models import Business

class ServiceCategory(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name} - {self.business.name}"

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    duration_mins = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.duration_mins}m)"

    @property
    def public_image_url(self):
        from core.image_defaults import first_usable_url

        upload = ""
        try:
            if self.image:
                upload = self.image.url
        except (ValueError, OSError):
            upload = ""
        return first_usable_url(
            upload,
            self.image_url,
            self.category.business.default_public_image_url,
        )

    @property
    def image_fallbacks(self):
        from core.image_defaults import placeholder_image_url

        return "|".join(
            [
                self.category.business.default_public_image_url,
                placeholder_image_url(),
            ]
        )

class BusinessHours(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), 
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='hours')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('business', 'day_of_week')

    def __str__(self):
        return f"{self.business.name} - {self.get_day_of_week_display()}"


class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    buy_url = models.URLField(blank=True, help_text="Optional external product / buy link")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    @property
    def public_image_url(self):
        from core.image_defaults import first_usable_url

        upload = ""
        try:
            if self.image:
                upload = self.image.url
        except (ValueError, OSError):
            upload = ""
        return first_usable_url(
            upload,
            self.image_url,
            self.business.default_public_image_url,
        )

    @property
    def image_fallbacks(self):
        from core.image_defaults import placeholder_image_url

        return "|".join(
            [
                self.business.default_public_image_url,
                placeholder_image_url(),
            ]
        )
