"""SEO helpers: absolute URLs, meta copy, LocalBusiness JSON-LD, programmatic pages."""

from __future__ import annotations

import json
import os
from urllib.parse import urljoin

from django.conf import settings
from django.utils.text import slugify


SITE_NAME = "SuratBazar"
DEFAULT_DESCRIPTION = (
    "Find and book trusted local businesses in Surat — salons, clinics, "
    "opticals, pet care and more. Compare prices, hours, and book online."
)

# Short plural labels for programmatic H1/titles
INDUSTRY_SEO_PLURAL = {
    "salon": "Salons & parlours",
    "spa": "Spas & wellness",
    "grooming": "Barbershops",
    "dentist": "Dentists",
    "clinic": "Clinics & doctors",
    "optical": "Optical shops",
    "physiotherapy": "Physiotherapy clinics",
    "ayurveda": "Ayurveda & homeopathy",
    "gym": "Gyms & fitness studios",
    "yoga": "Yoga & pilates",
    "restaurant": "Restaurants & cafés",
    "bakery": "Bakeries",
    "grocery": "Grocery stores",
    "fashion": "Fashion & boutiques",
    "pet": "Pet clinics & shops",
    "auto": "Auto services",
    "laundry": "Laundry services",
    "tailoring": "Tailors",
    "home_services": "Home services",
    "photography": "Photographers",
    "coaching": "Coaching & tuition",
    "events": "Event & wedding services",
    "legal": "Legal & consultants",
    "realestate": "Real estate",
    "other": "Local businesses",
}


def site_base_url(request=None) -> str:
    configured = (os.getenv("SITE_URL") or getattr(settings, "SITE_URL", "") or "").rstrip("/")
    if configured:
        return configured
    if request is not None:
        try:
            return request.build_absolute_uri("/").rstrip("/")
        except Exception:
            pass
    host = (os.getenv("DJANGO_ALLOWED_HOSTS") or "127.0.0.1").split(",")[0].strip()
    if host in {"*", ""}:
        host = "127.0.0.1"
    scheme = "https" if not settings.DEBUG else "http"
    return f"{scheme}://{host}"


def absolute_url(path: str, request=None) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = site_base_url(request)
    if not path.startswith("/"):
        path = f"/{path}"
    return urljoin(base + "/", path.lstrip("/"))


def truncate_meta(text: str, limit: int = 160) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def industry_seo_label(industry_key: str) -> str:
    from users.industries import industry_label

    return INDUSTRY_SEO_PLURAL.get(industry_key) or industry_label(industry_key)


def area_to_slug(area_label: str) -> str:
    return slugify(area_label or "") or ""


def business_meta_description(business) -> str:
    parts = []
    subtitle = (business.hero_subtitle or business.hero_title or "").strip()
    if subtitle:
        parts.append(subtitle)
    else:
        industry = business.get_industry_type_display()
        parts.append(f"{business.name} — {industry} in Surat. Book online on SuratBazar.")
    if (business.public_address or "").strip():
        parts.append(business.public_address.strip())
    return truncate_meta(" · ".join(parts))


def business_page_title(business) -> str:
    industry = business.get_industry_type_display()
    area = ""
    address = (business.public_address or "").strip()
    if address:
        area = address.split(",")[-1].strip()
        if area.lower() in {"india", "surat"} and "," in address:
            bits = [b.strip() for b in address.split(",") if b.strip()]
            if len(bits) >= 2:
                area = bits[-2] if bits[-1].lower() == "surat" else bits[-1]
    if area:
        return f"{business.name} — {industry} in {area} | SuratBazar"
    return f"{business.name} — {industry} | Book on SuratBazar"


def collection_page_meta(*, industry_key="", area_label="", count=0):
    """Title + description for /surat/ collection pages."""
    label = industry_seo_label(industry_key) if industry_key else "Local businesses"
    if area_label and industry_key:
        title = f"{label} in {area_label}, Surat | Book online | SuratBazar"
        description = (
            f"Find {count} {label.lower()} in {area_label}, Surat. "
            f"Compare hours, prices, and book appointments on SuratBazar."
        )
        h1 = f"{label} in {area_label}, Surat"
    elif industry_key:
        title = f"{label} in Surat | Book online | SuratBazar"
        description = (
            f"Browse {count} {label.lower()} in Surat. "
            f"See open hours, starting prices, and book online on SuratBazar."
        )
        h1 = f"{label} in Surat"
    else:
        title = "Local businesses in Surat | SuratBazar directory"
        description = (
            f"Explore {count} local businesses across Surat — salons, clinics, "
            f"opticals, pet care and more. Filter by category and area."
        )
        h1 = "Local businesses in Surat"
    return {
        "title": title,
        "description": truncate_meta(description),
        "h1": h1,
    }


def local_business_json_ld(business, request=None, services=None) -> str:
    """Build schema.org LocalBusiness JSON-LD for a public listing."""
    from core.plans import plan_allows_website, plan_shows_public_email

    url = absolute_url(f"/b/{business.slug}/", request)
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": business.name,
        "url": url,
        "image": business.public_hero_image_url,
        "description": business_meta_description(business),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": (business.public_address or "").strip() or None,
            "addressLocality": "Surat",
            "addressRegion": "Gujarat",
            "addressCountry": "IN",
        },
    }
    if (business.public_phone or "").strip():
        data["telephone"] = business.public_phone.strip()
    if plan_shows_public_email(business.listing_plan) and (
        business.public_email or ""
    ).strip():
        data["email"] = business.public_email.strip()
    website = (business.website_url or "").strip()
    if plan_allows_website(business.listing_plan) and website:
        data["sameAs"] = [website]

    if services:
        offers = []
        for service in services[:12]:
            offers.append(
                {
                    "@type": "Offer",
                    "name": service.name,
                    "price": str(service.price),
                    "priceCurrency": "INR",
                    "url": absolute_url(
                        f"/booking/{business.slug}/?service={service.id}", request
                    ),
                }
            )
        if offers:
            data["makesOffer"] = offers

    if data["address"].get("streetAddress") is None:
        data["address"].pop("streetAddress", None)

    return json.dumps(data, ensure_ascii=False)


def website_json_ld(request=None) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": site_base_url(request) + "/",
        "description": DEFAULT_DESCRIPTION,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": site_base_url(request) + "/?q={search_term_string}",
            },
            "query-input": "required name=search_term_string",
        },
    }
    return json.dumps(data, ensure_ascii=False)


def collection_json_ld(*, name, description, url, businesses, request=None) -> str:
    """ItemList JSON-LD for category/area landing pages."""
    elements = []
    for index, business in enumerate(businesses[:30], start=1):
        elements.append(
            {
                "@type": "ListItem",
                "position": index,
                "url": absolute_url(f"/b/{business.slug}/", request),
                "name": business.name,
            }
        )
    data = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": name,
        "description": description,
        "url": url,
        "isPartOf": {
            "@type": "WebSite",
            "name": SITE_NAME,
            "url": site_base_url(request) + "/",
        },
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(businesses),
            "itemListElement": elements,
        },
    }
    return json.dumps(data, ensure_ascii=False)


def breadcrumb_json_ld(crumbs, request=None) -> str:
    """crumbs: list of (name, path)"""
    items = []
    for i, (name, path) in enumerate(crumbs, start=1):
        items.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": name,
                "item": absolute_url(path, request),
            }
        )
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
    return json.dumps(data, ensure_ascii=False)
