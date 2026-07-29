import hashlib
import re
from collections import OrderedDict
from urllib.parse import quote_plus

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Exists, Max, Min, OuterRef, Q
from django.utils import timezone

from users.models import Business


DIRECTORY_CACHE_VERSION_KEY = "directory_cache_version"
# Cap rows hydrated for directory cards (full count uses lean COUNT).
DIRECTORY_HYDRATE_CAP = 48
DIRECTORY_OPEN_SCAN_CAP = 120


def _directory_cache_version():
    version = cache.get(DIRECTORY_CACHE_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(DIRECTORY_CACHE_VERSION_KEY, version, timeout=None)
    return version


def bust_directory_cache():
    """Invalidate cached directory listing results.

    Call after any write that changes what the public directory shows:
    business profile/plan changes, service or category changes, hours
    changes. Bumps a version stamp baked into every cache key instead of
    deleting individual keys (LocMemCache/Redis have no pattern-delete).
    """
    try:
        cache.incr(DIRECTORY_CACHE_VERSION_KEY)
    except ValueError:
        cache.set(DIRECTORY_CACHE_VERSION_KEY, 1, timeout=None)


def _directory_cache_key(**params):
    version = _directory_cache_version()
    raw = "|".join(f"{key}={params[key]}" for key in sorted(params))
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return f"directory_businesses:{version}:{digest}"


def industry_choices():
    """Return industry choices for directory filters."""
    return Business.INDUSTRY_CHOICES


def _phone_digits(phone):
    if not phone:
        return ""
    return re.sub(r"\D", "", phone)


def whatsapp_url_for_phone(phone):
    digits = _phone_digits(phone)
    if not digits:
        return ""
    if len(digits) == 10:
        digits = f"91{digits}"
    return f"https://wa.me/{digits}"


def maps_directions_url(address):
    address = (address or "").strip()
    if not address:
        return ""
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(address)}"


def price_range_label(min_price, max_price):
    if min_price is None:
        return ""
    min_fmt = f"{min_price:.2f}"
    if max_price is None or max_price == min_price:
        return f"₹{min_fmt}"
    return f"₹{min_fmt}–₹{max_price:.2f}"


def evaluate_open_status(hours_row, now_time=None):
    """
    Return (is_open_now, status, label) for a BusinessHours row.
    status: open | closed | unknown
    """
    if hours_row is None:
        return False, "unknown", "Hours unknown"

    if hours_row.is_closed:
        return False, "closed", "Closed today"

    if not hours_row.start_time or not hours_row.end_time:
        return False, "unknown", "Hours unknown"

    if now_time is None:
        now_time = timezone.localtime().time()

    start = hours_row.start_time
    end = hours_row.end_time
    start_label = start.strftime("%H:%M")
    end_label = end.strftime("%H:%M")

    # Overnight window (e.g. 22:00–02:00)
    if start <= end:
        is_open = start <= now_time <= end
    else:
        is_open = now_time >= start or now_time <= end

    if is_open:
        return True, "open", f"Open until {end_label}"
    if now_time < start if start <= end else now_time > end:
        return False, "closed", f"Opens at {start_label}"
    return False, "closed", f"Closed · was {start_label}–{end_label}"


def _lean_discoverable_queryset():
    """Discoverable businesses without heavy service/appointment annotations.

    Used for COUNT/facets/platform KPIs — much cheaper than _discoverable_queryset.
    """
    from catalog.models import Service

    has_active_service = Exists(
        Service.objects.filter(category__business_id=OuterRef("pk"), is_active=True)
    )
    return (
        Business.objects.filter(profile_setup_completed=True)
        .filter(has_active_service | ~Q(public_phone=""))
        .distinct()
    )


def _discoverable_queryset():
    """Annotated queryset for directory cards (prices, service counts, hours)."""
    return (
        Business.objects.annotate(
            service_count=Count(
                "categories__services",
                filter=Q(categories__services__is_active=True),
                distinct=True,
            ),
            starting_price=Min(
                "categories__services__price",
                filter=Q(categories__services__is_active=True),
            ),
            max_price=Max(
                "categories__services__price",
                filter=Q(categories__services__is_active=True),
            ),
            booking_count=Count(
                "appointments",
                filter=~Q(appointments__status="cancelled"),
                distinct=True,
            ),
            category_count=Count(
                "categories",
                filter=Q(categories__services__is_active=True),
                distinct=True,
            ),
        )
        .filter(
            Q(profile_setup_completed=True)
            & (
                Q(service_count__gt=0)
                | ~Q(public_phone="")
            )
        )
        # Categories + hours only — skip nested service prefetch (was the N×M cost).
        .prefetch_related("categories", "hours")
        .distinct()
    )


def _hydrate_directory_business(business, today_weekday, now_time):
    """Attach card-friendly derived fields onto a Business instance."""
    today_hours = None
    for row in business.hours.all():
        if row.day_of_week == today_weekday:
            today_hours = row
            break

    is_open, status, label = evaluate_open_status(today_hours, now_time=now_time)
    business.is_open_now = is_open
    business.today_status = status
    business.today_label = label
    business.is_verified = bool(
        business.profile_setup_completed
        and (business.public_phone or "").strip()
        and (business.public_address or "").strip()
        and (business.service_count or 0) > 0
    )
    from core.plans import (
        plan_allows_website,
        plan_card_style,
        plan_directory_rank,
        plan_has_pro_badge,
        plan_is_featured,
    )

    business.can_show_website = bool(
        plan_allows_website(business.listing_plan) and (business.website_url or "").strip()
    )
    business.is_featured_listing = plan_is_featured(business.listing_plan)
    business.has_pro_badge = plan_has_pro_badge(business.listing_plan)
    business.directory_rank = plan_directory_rank(business.listing_plan)
    business.card_style = plan_card_style(business.listing_plan)
    business.price_range_label = price_range_label(
        business.starting_price, business.max_price
    )
    business.whatsapp_url = whatsapp_url_for_phone(business.public_phone)
    business.maps_directions_url = maps_directions_url(business.public_address)
    business.is_bookable = (business.service_count or 0) > 0

    # Category names as chips (no nested service prefetch).
    category_names = []
    for category in business.categories.all():
        if category.name not in category_names:
            category_names.append(category.name)
        if len(category_names) >= 3:
            break
    business.top_services = category_names
    business.category_names = category_names
    business.area_label = extract_area_label(business.public_address)
    return business


def extract_area_label(address):
    address = (address or "").strip()
    if not address:
        return ""
    parts = [part.strip() for part in address.split(",") if part.strip()]
    if not parts:
        return ""
    if len(parts) >= 2 and parts[-1].lower() == "surat":
        return parts[-2]
    return parts[-1]


def area_slug_for_address(address):
    from core.seo import area_to_slug

    return area_to_slug(extract_area_label(address))


def list_directory_businesses(
    query="",
    industry="",
    sort="newest",
    availability="",
    bookable="",
    verified="",
    area_slug="",
    candidate_limit=None,
):
    """
    List publicly discoverable businesses for the home directory,
    hydrated with open-now, price range, and service preview fields.

    candidate_limit caps the queryset (after ordering, before hydration) to
    avoid hydrating an entire industry just to show a handful of results —
    used by callers like get_similar_businesses that only need a few rows
    and don't require exhaustive correctness across the full result set.

    When candidate_limit is omitted, a safe hydrate cap is applied so home /
    HTMX never materializes the full directory (use count_directory_businesses
    for totals). Area + open-now filters raise the scan cap.

    Results are cached for settings.DIRECTORY_CACHE_TTL seconds.
    """
    # Resolve hydrate cap early so it is part of the cache key.
    area_slug = (area_slug or "").strip().lower()
    availability = (availability or "").strip()
    if candidate_limit is None:
        if area_slug:
            candidate_limit = DIRECTORY_OPEN_SCAN_CAP
        elif availability == "open":
            candidate_limit = DIRECTORY_OPEN_SCAN_CAP
        else:
            candidate_limit = DIRECTORY_HYDRATE_CAP

    cache_key = _directory_cache_key(
        query=(query or "").strip(),
        industry=(industry or "").strip(),
        sort=(sort or "newest").strip(),
        availability=availability,
        bookable=(bookable or "").strip(),
        verified=(verified or "").strip(),
        area_slug=area_slug,
        candidate_limit=candidate_limit or "",
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    queryset = _apply_directory_filters(
        _discoverable_queryset(),
        query=query,
        industry=industry,
        bookable=bookable,
        verified=verified,
    )

    sort = (sort or "newest").strip()
    if sort == "name":
        queryset = queryset.order_by("name")
    elif sort == "services":
        queryset = queryset.order_by("-service_count", "name")
    elif sort == "popular":
        queryset = queryset.order_by("-booking_count", "-service_count", "name")
    elif sort == "price_low":
        queryset = queryset.order_by("starting_price", "name")
    elif sort == "price_high":
        queryset = queryset.order_by("-max_price", "name")
    else:
        queryset = queryset.order_by("-created_at", "name")

    if candidate_limit:
        queryset = queryset[:candidate_limit]

    today_weekday = timezone.localdate().weekday()
    now_time = timezone.localtime().time()
    businesses = [
        _hydrate_directory_business(b, today_weekday, now_time) for b in queryset
    ]

    if area_slug:
        businesses = [
            b
            for b in businesses
            if area_slug_for_address(b.public_address) == area_slug
        ]

    if availability == "open":
        businesses = [b for b in businesses if b.is_open_now]

    # Premium → Pro → Free placement, then keep selected queryset sort as tiebreaker.
    ranked = list(enumerate(businesses))
    ranked.sort(key=lambda item: (getattr(item[1], "directory_rank", 2), item[0]))
    result = [business for _, business in ranked]

    ttl = getattr(settings, "DIRECTORY_CACHE_TTL", 60)
    cache.set(cache_key, result, ttl)
    return result


def _apply_directory_filters(queryset, *, query="", industry="", bookable="", verified=""):
    query = (query or "").strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(hero_title__icontains=query)
            | Q(hero_subtitle__icontains=query)
            | Q(public_address__icontains=query)
            | Q(public_phone__icontains=query)
            | Q(categories__services__name__icontains=query)
            | Q(categories__name__icontains=query)
        ).distinct()

    industry = (industry or "").strip()
    if industry and industry in dict(Business.INDUSTRY_CHOICES):
        queryset = queryset.filter(industry_type=industry)

    if (bookable or "").strip() in ("1", "true", "yes"):
        from catalog.models import Service

        queryset = queryset.filter(
            Exists(
                Service.objects.filter(
                    category__business_id=OuterRef("pk"), is_active=True
                )
            )
        )

    if (verified or "").strip() in ("1", "true", "yes"):
        queryset = queryset.filter(profile_setup_completed=True).exclude(
            public_phone=""
        ).exclude(public_address="")

    return queryset


def count_directory_businesses(
    query="",
    industry="",
    bookable="",
    verified="",
    area_slug="",
):
    """Cheap COUNT for directory totals (no hydrate / nested prefetch)."""
    area_slug = (area_slug or "").strip().lower()
    cache_key = _directory_cache_key(
        kind="directory_count",
        query=(query or "").strip(),
        industry=(industry or "").strip(),
        bookable=(bookable or "").strip(),
        verified=(verified or "").strip(),
        area_slug=area_slug,
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    queryset = _apply_directory_filters(
        _lean_discoverable_queryset(),
        query=query,
        industry=industry,
        bookable=bookable,
        verified=verified,
    )

    if area_slug:
        # Area is derived from address — must inspect addresses (values only).
        count = 0
        for address in queryset.values_list("public_address", flat=True).iterator(
            chunk_size=500
        ):
            if area_slug_for_address(address) == area_slug:
                count += 1
    else:
        count = queryset.count()

    ttl = getattr(settings, "DIRECTORY_CACHE_TTL", 60)
    cache.set(cache_key, count, ttl)
    return count


def get_directory_stats(businesses):
    """KPI strip for the directory results set."""
    businesses = list(businesses)
    industries = {b.industry_type for b in businesses}
    return {
        "total": len(businesses),
        "open_now": sum(1 for b in businesses if getattr(b, "is_open_now", False)),
        "bookable": sum(1 for b in businesses if getattr(b, "is_bookable", False)),
        "verified": sum(1 for b in businesses if getattr(b, "is_verified", False)),
        "industries": len(industries),
    }


def get_platform_directory_stats():
    """Cached platform-wide KPIs for the home hero (no full directory hydrate)."""
    from catalog.models import BusinessHours, Service

    cache_key = _directory_cache_key(kind="platform_stats")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = _lean_discoverable_queryset()
    total = qs.count()
    has_service = Exists(
        Service.objects.filter(category__business_id=OuterRef("pk"), is_active=True)
    )
    bookable = qs.filter(has_service).count()
    verified = (
        qs.filter(has_service)
        .exclude(public_phone="")
        .exclude(public_address="")
        .count()
    )
    industries = (
        qs.order_by()
        .values("industry_type")
        .distinct()
        .count()
    )

    today_weekday = timezone.localdate().weekday()
    now_time = timezone.localtime().time()
    open_now = 0
    hours_qs = BusinessHours.objects.filter(
        day_of_week=today_weekday,
        business_id__in=qs.values("id"),
    ).only("business_id", "is_closed", "start_time", "end_time")
    for row in hours_qs.iterator(chunk_size=500):
        is_open, _, _ = evaluate_open_status(row, now_time=now_time)
        if is_open:
            open_now += 1

    result = {
        "total": total,
        "open_now": open_now,
        "bookable": bookable,
        "verified": verified,
        "industries": industries,
    }
    ttl = getattr(settings, "DIRECTORY_CACHE_TTL", 60)
    cache.set(cache_key, result, ttl)
    return result


def get_industry_facet_counts():
    """Industry counts across all discoverable businesses (for filter chips)."""
    cache_key = _directory_cache_key(kind="industry_facets")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    rows = (
        _lean_discoverable_queryset()
        .values("industry_type")
        .annotate(c=Count("id", distinct=True))
    )
    result = {row["industry_type"]: row["c"] for row in rows}
    ttl = getattr(settings, "DIRECTORY_CACHE_TTL", 60)
    cache.set(cache_key, result, ttl)
    return result


def get_area_facet_counts(industry=""):
    """
    Area labels + counts from public_address (programmatic SEO).
    Returns list of dicts: label, slug, count (sorted by count desc).
    """
    from collections import Counter

    from core.seo import area_to_slug

    industry = (industry or "").strip()
    cache_key = _directory_cache_key(kind="area_facets", industry=industry)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = _lean_discoverable_queryset().values_list("public_address", flat=True)
    if industry and industry in dict(Business.INDUSTRY_CHOICES):
        qs = qs.filter(industry_type=industry)

    counts = Counter()
    for address in qs.iterator(chunk_size=500):
        label = extract_area_label(address)
        if not label:
            continue
        counts[label] += 1

    rows = []
    for label, count in counts.items():
        slug = area_to_slug(label)
        if not slug:
            continue
        rows.append({"label": label, "slug": slug, "count": count})
    rows.sort(key=lambda row: (-row["count"], row["label"].lower()))

    ttl = getattr(settings, "DIRECTORY_CACHE_TTL", 60)
    cache.set(cache_key, rows, ttl)
    return rows


def resolve_area_label(area_slug, industry=""):
    """Map area URL slug back to a display label from live data."""
    area_slug = (area_slug or "").strip().lower()
    if not area_slug:
        return ""
    for row in get_area_facet_counts(industry=industry):
        if row["slug"] == area_slug:
            return row["label"]
    return ""


def get_industry_hub_rows():
    """Industries that currently have discoverable listings."""
    from core.seo import industry_seo_label

    counts = get_industry_facet_counts()
    rows = []
    for key, label in Business.INDUSTRY_CHOICES:
        count = counts.get(key, 0)
        if count <= 0:
            continue
        rows.append(
            {
                "key": key,
                "label": label,
                "seo_label": industry_seo_label(key),
                "count": count,
                "path": f"/surat/{key}/",
            }
        )
    rows.sort(key=lambda row: (-row["count"], row["label"].lower()))
    return rows


def get_similar_businesses(business, limit=4):
    """Other directory businesses in the same industry (Pro+ listing pages)."""
    from core.plans import plan_shows_similar_businesses

    if not plan_shows_similar_businesses(business.listing_plan):
        return []
    similar = list_directory_businesses(
        industry=business.industry_type,
        sort="popular",
        candidate_limit=max(limit * 5, 20),
    )
    return [item for item in similar if item.id != business.id][:limit]


def get_business_listing_context(business, services):
    """Build extra context for richer public business listing pages."""
    from catalog.models import BusinessHours
    from booking.models import Appointment

    hours = list(
        BusinessHours.objects.filter(business=business).order_by("day_of_week")
    )
    today_weekday = timezone.localdate().weekday()
    today_hours = next((row for row in hours if row.day_of_week == today_weekday), None)
    now_time = timezone.localtime().time()
    is_open_now, today_status, today_label = evaluate_open_status(
        today_hours, now_time=now_time
    )

    prices = [service.price for service in services]
    durations = [service.duration_mins for service in services]
    starting_price = min(prices) if prices else None
    max_price = max(prices) if prices else None
    min_duration = min(durations) if durations else None
    max_duration = max(durations) if durations else None

    booking_qs = Appointment.objects.filter(business=business).exclude(status="cancelled")
    booking_agg = booking_qs.aggregate(
        booking_count=Count("id"),
        completed_count=Count("id", filter=Q(status="completed")),
    )
    booking_count = booking_agg["booking_count"] or 0
    completed_count = booking_agg["completed_count"] or 0

    from catalog.models import Product
    from core.plans import (
        get_plan_config,
        plan_allows_products,
        plan_allows_website,
        plan_featured_services_limit,
        plan_has_pro_badge,
        plan_hides_platform_branding,
        plan_is_featured,
        plan_product_limit,
        plan_shows_map_embed,
        plan_shows_public_email,
        plan_shows_share_tools,
        plan_shows_testimonial,
    )

    featured_limit = plan_featured_services_limit(business.listing_plan)

    # Popular services by appointment volume (count gated by plan)
    popular_ids = list(
        booking_qs.values("service_id")
        .annotate(c=Count("id"))
        .order_by("-c")
        .values_list("service_id", flat=True)[:featured_limit]
    )
    service_by_id = {s.id: s for s in services}
    popular_services = [service_by_id[sid] for sid in popular_ids if sid in service_by_id]
    if not popular_services:
        popular_services = sorted(services, key=lambda s: s.price)[:featured_limit]

    services_by_category = OrderedDict()
    for service in services:
        cat_name = service.category.name
        services_by_category.setdefault(cat_name, []).append(service)

    category_groups = [
        {"name": name, "index": index, "services": items}
        for index, (name, items) in enumerate(services_by_category.items(), start=1)
    ]

    plan = get_plan_config(business.listing_plan)
    products = []
    if plan_allows_products(business.listing_plan):
        product_limit = plan_product_limit(business.listing_plan)
        products_qs = Product.objects.filter(business=business, is_active=True).order_by("name")
        if product_limit is not None:
            products = list(products_qs[:product_limit])
        else:
            products = list(products_qs)

    website_url = (business.website_url or "").strip()
    can_show_website = plan_allows_website(business.listing_plan) and bool(website_url)
    map_embed_url = (business.map_embed_url or "").strip()
    testimonial_quote = (business.testimonial_quote or "").strip()
    can_show_map = plan_shows_map_embed(business.listing_plan) and bool(map_embed_url)
    can_show_testimonial = plan_shows_testimonial(business.listing_plan) and bool(
        testimonial_quote
    )
    can_show_public_email = plan_shows_public_email(business.listing_plan) and bool(
        (business.public_email or "").strip()
    )

    return {
        "business_hours": hours,
        "today_hours": today_hours,
        "is_open_now": is_open_now,
        "today_status": today_status,
        "today_label": today_label,
        "service_count": len(services),
        "starting_price": starting_price,
        "max_price": max_price,
        "price_range_label": price_range_label(starting_price, max_price),
        "min_duration": min_duration,
        "max_duration": max_duration,
        "booking_count": booking_count,
        "completed_count": completed_count,
        "services_by_category": services_by_category,
        "category_groups": category_groups,
        "popular_services": popular_services,
        "products": products,
        "whatsapp_url": whatsapp_url_for_phone(business.public_phone),
        "maps_directions_url": maps_directions_url(business.public_address),
        "member_since": business.created_at,
        "is_verified": bool(
            business.profile_setup_completed
            and (business.public_phone or "").strip()
            and (business.public_address or "").strip()
            and len(services) > 0
        ),
        "is_bookable": len(services) > 0,
        "category_count": len(services_by_category),
        "plan": plan,
        "can_show_website": can_show_website,
        "public_website_url": website_url if can_show_website else "",
        "is_featured_listing": plan_is_featured(business.listing_plan),
        "has_pro_badge": plan_has_pro_badge(business.listing_plan),
        "can_show_map": can_show_map,
        "public_map_embed_url": map_embed_url if can_show_map else "",
        "can_show_testimonial": can_show_testimonial,
        "can_show_public_email": can_show_public_email,
        "can_show_share_tools": plan_shows_share_tools(business.listing_plan),
        "hide_platform_branding": plan_hides_platform_branding(business.listing_plan),
    }
