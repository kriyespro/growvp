"""Shared default / fallback image paths for listings, products, and services."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings

# Local assets — always available (no remote 404s).
PLACEHOLDER_STATIC = "img/placeholder.svg"
LISTING_DEFAULT_STATIC = "img/listing-default.webp"
LISTING_DEFAULT_FALLBACK_STATIC = "img/listing-default.jpg"


def _static_url(path: str) -> str:
    base = (getattr(settings, "STATIC_URL", None) or "/static/").rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def placeholder_image_url():
    return _static_url(PLACEHOLDER_STATIC)


def listing_default_image_url():
    """Reliable on-site default card image (WebP)."""
    return _static_url(LISTING_DEFAULT_STATIC)


def listing_default_jpg_url():
    return _static_url(LISTING_DEFAULT_FALLBACK_STATIC)


def first_usable_url(*candidates):
    """Return the first non-empty http(s) or /static URL from candidates."""
    for value in candidates:
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        if not cleaned:
            continue
        # Skip obvious junk that would white-screen
        if cleaned.lower() in {"none", "null", "undefined", "-"}:
            continue
        if cleaned.startswith(("http://", "https://", "/")):
            return cleaned
    return listing_default_image_url()


def optimize_image_url(url: str, width: int = 480, quality: int = 45) -> str:
    """
    Shrink remote Unsplash images for cards. Leaves local/static URLs alone.
    """
    if not url or not isinstance(url, str):
        return url or ""
    cleaned = url.strip()
    if not cleaned.startswith("http"):
        return cleaned

    parts = urlsplit(cleaned)
    host = (parts.netloc or "").lower()
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    if "images.unsplash.com" in host:
        query["auto"] = "format"
        query["fit"] = "crop"
        query["w"] = str(width)
        query["q"] = str(quality)
        # Do not force fm=webp — some photo IDs 404 with it
        query.pop("fm", None)
        query.pop("h", None)
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )

    return cleaned


def image_srcset(
    url: str,
    widths: tuple[int, ...] | list[int] = (320, 480, 640),
    quality: int = 45,
) -> str:
    """Responsive srcset for Unsplash only (local defaults skip srcset)."""
    if not url or "images.unsplash.com" not in url:
        return ""
    parts = []
    for w in widths:
        parts.append(f"{optimize_image_url(url, width=int(w), quality=quality)} {int(w)}w")
    return ", ".join(parts)
