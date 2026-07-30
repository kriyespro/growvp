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
    # Optional SEO overrides — blank = programmatic defaults from core.seo
    seo_title = models.CharField(
        max_length=70,
        blank=True,
        help_text="Custom <title> / og:title (≤70 chars). Leave blank for auto.",
    )
    seo_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Custom meta description (≤160 chars). Leave blank for auto.",
    )
    seo_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated keywords. Leave blank for auto.",
    )
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
        """Stable local default — remote Unsplash IDs often 404 (e.g. optical)."""
        from core.image_defaults import listing_default_image_url

        return listing_default_image_url()

    @property
    def public_hero_image_url(self):
        """Prefer saved hero_image_url; fall back to on-site default image."""
        from core.image_defaults import first_usable_url

        return first_usable_url(
            self.hero_image_url,
            self.default_public_image_url,
        )

    @property
    def image_fallbacks(self):
        """Chain for onerror: category/local default → jpg → svg placeholder."""
        from core.image_defaults import (
            listing_default_image_url,
            listing_default_jpg_url,
            placeholder_image_url,
        )

        primary = self.public_hero_image_url
        urls = []
        for candidate in (
            listing_default_image_url(),
            listing_default_jpg_url(),
            placeholder_image_url(),
        ):
            if candidate and candidate != primary and candidate not in urls:
                urls.append(candidate)
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
