from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

class Business(models.Model):
    INDUSTRY_CHOICES = [
        ('salon', 'Salon / Parlour'),
        ('dentist', 'Dentist Clinic'),
        ('optical', 'Optical Shop'),
        ('pet', 'Pet Shop / Clinic'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=255)
    industry_type = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)
    timezone = models.CharField(max_length=50, default='UTC')
    upi_id = models.CharField(max_length=50, blank=True, help_text="e.g. yourname@paytm")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    hero_title = models.CharField(max_length=255, blank=True)
    hero_subtitle = models.TextField(blank=True)
    hero_image_url = models.URLField(blank=True)
    public_phone = models.CharField(max_length=20, blank=True)
    public_email = models.EmailField(blank=True)
    public_address = models.TextField(blank=True)
    map_embed_url = models.URLField(blank=True)
    testimonial_quote = models.TextField(blank=True)
    testimonial_author = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "business"
            slug = base_slug
            index = 1
            while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                index += 1
                slug = f"{base_slug}-{index}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class User(AbstractUser):
    # Overriding to make email unique for this SaaS
    email = models.EmailField(unique=True)
    
    def __str__(self):
        return self.email

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('receptionist', 'Receptionist'),
        ('provider', 'Service Provider'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()}) at {self.business.name}"
