from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from core.plans import PLAN_COMPARE_ROWS, PLAN_CONFIG
from core.seo import (
    absolute_url,
    breadcrumb_json_ld,
    business_meta_description,
    business_page_title,
    collection_json_ld,
    collection_page_meta,
    industry_seo_label,
    local_business_json_ld,
    website_json_ld,
)
from core.services import (
    get_area_facet_counts,
    get_business_listing_context,
    get_directory_stats,
    get_industry_facet_counts,
    get_industry_hub_rows,
    get_similar_businesses,
    industry_choices,
    list_directory_businesses,
    resolve_area_label,
)

# Home / HTMX directory: keep the page light (20–30 range)
DIRECTORY_LIST_LIMIT = 24


def _directory_context(request):
    query = request.GET.get("q", "")
    industry = request.GET.get("industry", "")
    sort = request.GET.get("sort", "newest")
    availability = request.GET.get("availability", "")
    bookable = request.GET.get("bookable", "")
    verified = request.GET.get("verified", "")
    businesses = list_directory_businesses(
        query=query,
        industry=industry,
        sort=sort,
        availability=availability,
        bookable=bookable,
        verified=verified,
    )
    total_count = len(businesses)
    stats = get_directory_stats(businesses)
    open_now_featured = []
    if availability != "open":
        open_candidates = [b for b in businesses if b.is_open_now]
        open_candidates.sort(
            key=lambda b: (
                getattr(b, "directory_rank", 2),
                -(b.booking_count or 0),
            )
        )
        open_now_featured = open_candidates[:4]
    page_businesses = businesses[:DIRECTORY_LIST_LIMIT]
    return {
        "businesses": page_businesses,
        "q": query,
        "industry": industry,
        "sort": sort,
        "availability": availability,
        "bookable": bookable,
        "verified": verified,
        "industries": industry_choices(),
        "industry_counts": get_industry_facet_counts(),
        "result_count": len(page_businesses),
        "total_count": total_count,
        "list_limited": total_count > DIRECTORY_LIST_LIMIT,
        "stats": stats,
        "open_now_featured": open_now_featured,
    }


@ensure_csrf_cookie
def landing(request):
    ctx = _directory_context(request)
    ctx["website_json_ld"] = website_json_ld(request)
    ctx["canonical_url"] = absolute_url("/", request)
    ctx["industry_hub_rows"] = get_industry_hub_rows()[:8]
    ctx["area_hub_rows"] = get_area_facet_counts()[:6]
    # Platform-wide KPIs (unfiltered) for hero strip
    all_listings = list_directory_businesses()
    ctx["home_stats"] = get_directory_stats(all_listings)
    featured = [b for b in all_listings if getattr(b, "is_featured_listing", False)]
    if len(featured) < 3:
        featured = all_listings[:3]
    else:
        featured = featured[:3]
    ctx["featured_businesses"] = featured
    return render(request, "pages/landing.jinja", ctx)


@require_GET
def pricing(request):
    """Public pricing page — yearly plans + compare table."""
    return render(
        request,
        "pages/pricing.jinja",
        {
            "plans": list(PLAN_CONFIG.values()),
            "compare_rows": PLAN_COMPARE_ROWS,
            "canonical_url": absolute_url("/pricing/", request),
        },
    )


@require_GET
def directory_search(request):
    """HTMX partial for live directory search/filter results."""
    return render(
        request,
        "partials/_business_directory_results.jinja",
        _directory_context(request),
    )


@ensure_csrf_cookie
def business_landing(request, business_slug):
    from django.shortcuts import get_object_or_404
    from users.models import Business
    from catalog.models import Service
    from core.services import area_slug_for_address, extract_area_label

    business = get_object_or_404(Business, slug=business_slug)
    services = list(
        Service.objects.filter(category__business=business, is_active=True)
        .select_related("category")
        .order_by("category__name", "name")
    )
    industry = business.industry_type or ""
    area_label = extract_area_label(business.public_address)
    area_slug = area_slug_for_address(business.public_address)
    crumbs = [("SuratBazar", "/"), ("Surat", "/surat/")]
    if industry:
        crumbs.append((industry_seo_label(industry), f"/surat/{industry}/"))
    if area_label and area_slug and industry:
        crumbs.append(
            (area_label, f"/surat/{industry}/{area_slug}/")
        )
    crumbs.append((business.name, f"/b/{business.slug}/"))
    context = {
        "business": business,
        "services": services,
        **get_business_listing_context(business, services),
        "similar_businesses": get_similar_businesses(business),
        "page_title": business_page_title(business),
        "meta_description": business_meta_description(business),
        "canonical_url": absolute_url(f"/b/{business.slug}/", request),
        "og_image_url": business.public_hero_image_url,
        "local_business_json_ld": local_business_json_ld(
            business, request=request, services=services
        ),
        "breadcrumb_json_ld": breadcrumb_json_ld(crumbs, request),
        "seo_industry": industry,
        "seo_industry_label": industry_seo_label(industry) if industry else "",
        "seo_area_label": area_label,
        "seo_area_slug": area_slug,
    }
    return render(request, "pages/public/business_landing.jinja", context)


@require_GET
def robots_txt(request):
    base = absolute_url("/", request).rstrip("/")
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Allow: /surat/",
            "Allow: /b/",
            "Allow: /pricing/",
            "Allow: /booking/",
            "Disallow: /admin/",
            "Disallow: /sd/",
            "Disallow: /dashboard/",
            "Disallow: /partner/",
            "Disallow: /account/",
            "Disallow: /leads/",
            "Disallow: /auth/",
            "Disallow: /catalog/",
            "Disallow: /crm/",
            "Disallow: /billing/",
            f"Sitemap: {base}/sitemap.xml",
            "",
        ]
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@require_GET
def sitemap_xml(request):
    """Dynamic Google sitemap — cached to avoid cold-start timeouts."""
    from django.conf import settings
    from django.core.cache import cache

    from core.seo import build_sitemap_entries, render_sitemap_xml, site_base_url
    from core.services import _directory_cache_version

    base = site_base_url(request)
    cache_key = f"sitemap_xml_v2:{base}:v{_directory_cache_version()}"
    body = cache.get(cache_key)
    if body is None:
        body = render_sitemap_xml(build_sitemap_entries(request))
        cache.set(cache_key, body, getattr(settings, "DIRECTORY_CACHE_TTL", 60) * 10)
    return HttpResponse(body, content_type="application/xml; charset=utf-8")


def _collection_open_now(businesses, limit=8):
    open_now = [b for b in businesses if b.is_open_now]
    open_now.sort(key=lambda b: (getattr(b, "directory_rank", 2), -(b.booking_count or 0)))
    return open_now[:limit]


@require_GET
def surat_hub(request):
    """City hub — all categories with listings."""
    industries = get_industry_hub_rows()
    areas = get_area_facet_counts()[:24]
    total = sum(row["count"] for row in industries)
    meta = collection_page_meta(count=total)
    path = "/surat/"
    canonical = absolute_url(path, request)
    crumbs = [("SuratBazar", "/"), ("Surat", path)]
    return render(
        request,
        "pages/seo/surat_hub.jinja",
        {
            "industries": industries,
            "areas": areas,
            "page_title": meta["title"],
            "meta_description": meta["description"],
            "h1": meta["h1"],
            "canonical_url": canonical,
            "collection_json_ld": collection_json_ld(
                name=meta["h1"],
                description=meta["description"],
                url=canonical,
                businesses=[],
                request=request,
            ),
            "breadcrumb_json_ld": breadcrumb_json_ld(crumbs, request),
            "total_listings": total,
        },
    )


@require_GET
def surat_industry(request, industry):
    """Category landing: /surat/<industry>/"""
    from users.models import Business
    from django.http import Http404

    industry = (industry or "").strip()
    if industry not in dict(Business.INDUSTRY_CHOICES):
        raise Http404("Unknown category")

    businesses = list_directory_businesses(industry=industry, sort="popular")
    total_count = len(businesses)
    page_businesses = businesses[:DIRECTORY_LIST_LIMIT]
    areas = get_area_facet_counts(industry=industry)
    meta = collection_page_meta(industry_key=industry, count=total_count)
    path = f"/surat/{industry}/"
    canonical = absolute_url(path, request)
    crumbs = [
        ("SuratBazar", "/"),
        ("Surat", "/surat/"),
        (industry_seo_label(industry), path),
    ]
    related = [
        row for row in get_industry_hub_rows() if row["key"] != industry
    ][:8]
    return render(
        request,
        "pages/seo/surat_collection.jinja",
        {
            "industry": industry,
            "industry_label": industry_seo_label(industry),
            "area_label": "",
            "area_slug": "",
            "businesses": page_businesses,
            "total_count": total_count,
            "list_limited": total_count > DIRECTORY_LIST_LIMIT,
            "areas": areas,
            "related_industries": related,
            "stats": get_directory_stats(businesses),
            "open_now_featured": _collection_open_now(businesses),
            "page_title": meta["title"],
            "meta_description": meta["description"],
            "h1": meta["h1"],
            "canonical_url": canonical,
            "collection_json_ld": collection_json_ld(
                name=meta["h1"],
                description=meta["description"],
                url=canonical,
                businesses=businesses,
                request=request,
            ),
            "breadcrumb_json_ld": breadcrumb_json_ld(crumbs, request),
        },
    )


@require_GET
def surat_industry_area(request, industry, area_slug):
    """Area × category landing: /surat/<industry>/<area>/"""
    from users.models import Business
    from django.http import Http404

    industry = (industry or "").strip()
    area_slug = (area_slug or "").strip().lower()
    if industry not in dict(Business.INDUSTRY_CHOICES):
        raise Http404("Unknown category")

    area_label = resolve_area_label(area_slug, industry=industry)
    if not area_label:
        # Fallback: try global areas (same slug may match another industry)
        area_label = resolve_area_label(area_slug, industry="")
    if not area_label:
        raise Http404("Unknown area")

    businesses = list_directory_businesses(
        industry=industry, area_slug=area_slug, sort="popular"
    )
    if not businesses:
        raise Http404("No listings in this area yet")

    total_count = len(businesses)
    page_businesses = businesses[:DIRECTORY_LIST_LIMIT]
    meta = collection_page_meta(
        industry_key=industry, area_label=area_label, count=total_count
    )
    path = f"/surat/{industry}/{area_slug}/"
    canonical = absolute_url(path, request)
    crumbs = [
        ("SuratBazar", "/"),
        ("Surat", "/surat/"),
        (industry_seo_label(industry), f"/surat/{industry}/"),
        (area_label, path),
    ]
    sibling_areas = [
        row
        for row in get_area_facet_counts(industry=industry)
        if row["slug"] != area_slug
    ][:10]
    return render(
        request,
        "pages/seo/surat_collection.jinja",
        {
            "industry": industry,
            "industry_label": industry_seo_label(industry),
            "area_label": area_label,
            "area_slug": area_slug,
            "businesses": page_businesses,
            "total_count": total_count,
            "list_limited": total_count > DIRECTORY_LIST_LIMIT,
            "areas": sibling_areas,
            "related_industries": [
                row for row in get_industry_hub_rows() if row["key"] != industry
            ][:8],
            "stats": get_directory_stats(businesses),
            "open_now_featured": _collection_open_now(businesses),
            "page_title": meta["title"],
            "meta_description": meta["description"],
            "h1": meta["h1"],
            "canonical_url": canonical,
            "collection_json_ld": collection_json_ld(
                name=meta["h1"],
                description=meta["description"],
                url=canonical,
                businesses=businesses,
                request=request,
            ),
            "breadcrumb_json_ld": breadcrumb_json_ld(crumbs, request),
        },
    )


@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def dashboard(request):
    from django.shortcuts import redirect
    from users.services import home_url_for_user

    user = request.user
    if user.platform_role != "business":
        return redirect(home_url_for_user(user))

    try:
        profile = getattr(user, 'profile', None)
    except Exception:
        profile = None
    
    if not profile or not profile.business_id:
        return redirect(home_url_for_user(user))
    if not profile.business.is_profile_ready:
        return redirect('/auth/business-profile/?onboarding=1')

    context = {
        'business': profile.business,
        'role': profile.role
    }
    return render(request, 'pages/dashboard.jinja', context)

@login_required(login_url='/auth/login/')
def dashboard_home(request):
    from django.shortcuts import redirect
    from users.services import home_url_for_user

    if request.user.platform_role != "business":
        return redirect(home_url_for_user(request.user))

    try:
        profile = getattr(request.user, 'profile', None)
    except Exception:
        profile = None
    
    if not profile or not profile.business_id:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)

    business = profile.business
    
    import datetime
    from django.utils import timezone
    from booking.models import Appointment
    from crm.models import Customer
    from billing.models import Invoice
    from django.db.models import Sum
    
    today = timezone.now().date()
    
    # Today's Revenue
    today_revenue = Invoice.objects.filter(
        business=business, 
        status='paid',
        created_at__date=today
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    
    # Appointments Today
    today_appointments = Appointment.objects.filter(
        business=business,
        date=today
    ).count()
    
    # Total Clients
    total_clients = Customer.objects.filter(business=business).count()
    
    # No Shows
    total_appointments = Appointment.objects.filter(business=business).count()
    no_shows = Appointment.objects.filter(business=business, status='no-show').count()
    no_show_rate = int((no_shows / total_appointments) * 100) if total_appointments > 0 else 0
    
    context = {
        'business': business,
        'today_revenue': today_revenue,
        'today_revenue_display': f"{today_revenue:.2f}",
        'today_appointments': today_appointments,
        'total_clients': total_clients,
        'no_show_rate': no_show_rate,
    }
    return render(request, 'partials/_dashboard_home.jinja', context)
