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
    profile_setup_completed = models.BooleanField(default=False)
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

    @property
    def is_profile_ready(self):
        return self.profile_setup_completed

    @property
    def default_public_image_url(self):
        defaults = {
            'dentist': 'https://images.unsplash.com/photo-1677026010083-78ec7f1b84ed?w=900&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MjR8fGRlbnRpc3R8ZW58MHx8MHx8fDA%3D',
            'pet': 'https://images.unsplash.com/photo-1517948430535-1e2469d314fe?q=80&w=1740&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
            'salon': 'https://images.unsplash.com/photo-1690749138086-7422f71dc159?q=80&w=654&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        }
        return defaults.get(
            self.industry_type,
            'https://images.unsplash.com/photo-1690749138086-7422f71dc159?q=80&w=654&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        )

    @property
    def public_hero_image_url(self):
        return self.hero_image_url or self.default_public_image_url

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
