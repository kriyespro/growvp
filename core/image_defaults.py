"""Shared default / fallback image paths for listings, products, and services."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


def optimize_image_url(url: str, width: int = 480, quality: int = 45) -> str:
    """
    Shrink remote images for cards (Unsplash params). Leaves local/static URLs alone.
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
        # Prefer modern formats when Unsplash supports fm=
        query.setdefault("fm", "webp")
        # Drop oversized legacy params
        query.pop("h", None)
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )

    return cleaned


def image_srcset(
    url: str,
    widths: tuple[int, ...] = (320, 480, 640),
    quality: int = 45,
) -> str:
    """Responsive srcset for Unsplash (capped at 640w for card grids)."""
    if not url:
        return ""
    if "images.unsplash.com" not in url:
        return ""
    parts = []
    for w in widths:
        parts.append(f"{optimize_image_url(url, width=w, quality=quality)} {w}w")
    return ", ".join(parts)
