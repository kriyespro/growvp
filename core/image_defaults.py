"""Shared default / fallback image paths for listings, products, and services."""

from django.conf import settings

# Local SVG always available even if remote hero/product URLs break.
PLACEHOLDER_STATIC = "img/placeholder.svg"


def placeholder_image_url():
    # Prefer plain STATIC_URL path so tests/ManifestStaticFiles don't require collectstatic.
    base = (getattr(settings, "STATIC_URL", None) or "/static/").rstrip("/")
    return f"{base}/{PLACEHOLDER_STATIC}"


def first_usable_url(*candidates):
    """Return the first non-empty string URL from candidates."""
    for value in candidates:
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                return cleaned
    return placeholder_image_url()
