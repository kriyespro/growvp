from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

from users.industries import INDUSTRY_GROUPS, industry_choices_flat


class Business(models.Model):
    INDUSTRY_CHOICES = industry_choices_flat()
    INDUSTRY_GROUPS = INDUSTRY_GROUPS
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
        ("premium", "Premium"),
    ]
    name = models.CharField(max_length=255)
    industry_type = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)
    timezone = models.CharField(max_length=50, default="UTC")
    upi_id = models.CharField(max_length=50, blank=True, help_text="e.g. yourname@paytm")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    hero_title = models.CharField(max_length=255, blank=True)
    hero_subtitle = models.TextField(blank=True)
    hero_image_url = models.URLField(blank=True)
    public_phone = models.CharField(max_length=20, blank=True)
    public_email = models.EmailField(blank=True)
    public_address = models.TextField(blank=True)
    website_url = models.URLField(blank=True, help_text="Public business website")
    map_embed_url = models.URLField(blank=True)
    testimonial_quote = models.TextField(blank=True)
    testimonial_author = models.CharField(max_length=150, blank=True)
    listing_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    profile_setup_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_businesses",
    )
    assigned_partners = models.ManyToManyField(
        "User",
        blank=True,
        related_name="assigned_businesses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['industry_type']),
            models.Index(fields=['profile_setup_completed']),
        ]

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
            "salon": "https://images.unsplash.com/photo-1690749138086-7422f71dc159?q=80&w=654&auto=format&fit=crop",
            "spa": "https://images.unsplash.com/photo-1540555700474-0649585eb711?q=80&w=800&auto=format&fit=crop",
            "grooming": "https://images.unsplash.com/photo-1621605815971-fbc98d665033?q=80&w=800&auto=format&fit=crop",
            "dentist": "https://images.unsplash.com/photo-1677026010083-78ec7f1b84ed?w=900&auto=format&fit=crop",
            "clinic": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?q=80&w=800&auto=format&fit=crop",
            "optical": "https://images.unsplash.com/photo-1574259406477-12687b0c497a?q=80&w=800&auto=format&fit=crop",
            "physiotherapy": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?q=80&w=800&auto=format&fit=crop",
            "gym": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=800&auto=format&fit=crop",
            "yoga": "https://images.unsplash.com/photo-1545205597-3d9d02c29597?q=80&w=800&auto=format&fit=crop",
            "restaurant": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=800&auto=format&fit=crop",
            "bakery": "https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=800&auto=format&fit=crop",
            "pet": "https://images.unsplash.com/photo-1517948430535-1e2469d314fe?q=80&w=800&auto=format&fit=crop",
            "auto": "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?q=80&w=800&auto=format&fit=crop",
            "photography": "https://images.unsplash.com/photo-1452587925148-ce544e57ee08?q=80&w=800&auto=format&fit=crop",
        }
        return defaults.get(
            self.industry_type,
            "https://images.unsplash.com/photo-1690749138086-7422f71dc159?q=80&w=654&auto=format&fit=crop",
        )

    @property
    def public_hero_image_url(self):
        from core.image_defaults import first_usable_url
        from core.plans import plan_allows_custom_hero

        if plan_allows_custom_hero(self.listing_plan):
            return first_usable_url(
                self.hero_image_url,
                self.default_public_image_url,
            )
        return self.default_public_image_url

    @property
    def image_fallbacks(self):
        from core.image_defaults import placeholder_image_url

        primary = self.public_hero_image_url
        default = self.default_public_image_url
        placeholder = placeholder_image_url()
        urls = []
        if primary != default:
            urls.append(default)
        if placeholder not in urls and placeholder != primary:
            urls.append(placeholder)
        return "|".join(urls)

    @property
    def is_pro(self):
        return self.listing_plan in ("pro", "premium")

    @property
    def is_premium(self):
        return self.listing_plan == "premium"

    @property
    def plan_label(self):
        return dict(self.PLAN_CHOICES).get(self.listing_plan, "Free")


class User(AbstractUser):
    PLATFORM_ROLE_CHOICES = [
        ("super_admin", "Super Admin"),
        ("marketing_partner", "Marketing Partner"),
        ("business", "Business"),
        ("client", "Client"),
    ]

    email = models.EmailField(unique=True)
    platform_role = models.CharField(
        max_length=32,
        choices=PLATFORM_ROLE_CHOICES,
        default="business",
        db_index=True,
    )

    def __str__(self):
        return self.email

    @property
    def is_platform_super_admin(self):
        return self.platform_role == "super_admin" or self.is_superuser

    @property
    def is_marketing_partner(self):
        return self.platform_role == "marketing_partner"

    @property
    def is_business_user(self):
        return self.platform_role == "business"

    @property
    def is_client_user(self):
        return self.platform_role == "client"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("receptionist", "Receptionist"),
        ("provider", "Service Provider"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="staff",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        if self.business_id:
            return f"{self.user.email} ({self.get_role_display()}) at {self.business.name}"
        return f"{self.user.email} ({self.get_role_display()})"
