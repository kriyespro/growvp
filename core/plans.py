"""
Listing plan ladder (yearly).

  FREE     → Get discovered + take bookings
  PRO      → Convert visitors (website, products, trust tools)
  PREMIUM  → Dominate demand (featured + unlimited + no branding)
"""

PLAN_CONFIG = {
    "free": {
        "key": "free",
        "name": "Free",
        "price_yearly": 0,
        "price_label": "₹0",
        "billing_label": "per year",
        "tagline": "Get listed and start taking bookings",
        "service_limit": 5,
        "product_limit": 0,
        "website_enabled": False,
        "pro_badge": False,
        "featured": False,
        "open_now_priority": 2,
        "directory_rank": 2,
        "featured_services_limit": 1,
        "custom_hero": True,
        "show_map_embed": False,
        "show_testimonial": False,
        "show_public_email": False,
        "show_share_tools": False,
        "show_similar_businesses": False,
        "hide_platform_branding": False,
        "card_style": "standard",
        "features": [
            "Public listing in SuratBazar directory",
            "Phone, WhatsApp & directions",
            "Opening hours + Open now status",
            "Custom listing photo on home & profile",
            "Online appointment booking",
            "Up to 5 bookable services",
            "1 featured service highlight",
        ],
        "not_included": [
            "Website button",
            "Product listings",
            "Map embed & testimonials",
            "Share tools",
            "Featured directory placement",
        ],
    },
    "pro": {
        "key": "pro",
        "name": "Pro",
        "price_yearly": 999,
        "price_label": "₹999",
        "billing_label": "per year",
        "tagline": "Convert more — website, products & trust tools",
        "service_limit": 25,
        "product_limit": 15,
        "website_enabled": True,
        "pro_badge": True,
        "featured": False,
        "open_now_priority": 1,
        "directory_rank": 1,
        "featured_services_limit": 3,
        "custom_hero": True,
        "show_map_embed": True,
        "show_testimonial": True,
        "show_public_email": True,
        "show_share_tools": True,
        "show_similar_businesses": True,
        "hide_platform_branding": False,
        "card_style": "highlight",
        "features": [
            "Everything in Free",
            "Website button on your public page",
            "Up to 15 product listings",
            "Up to 25 bookable services",
            "Pro badge on cards & listing",
            "Custom hero image",
            "Map embed + customer testimonial",
            "Public email + share/link tools",
            "3 featured service highlights",
            "Highlighted directory card",
            "Appear in “More like this”",
        ],
        "not_included": [
            "Featured top placement",
            "Unlimited catalog",
            "Remove SuratBazar branding",
        ],
    },
    "premium": {
        "key": "premium",
        "name": "Premium",
        "price_yearly": 3999,
        "price_label": "₹3,999",
        "billing_label": "per year",
        "tagline": "Own the directory — featured + unlimited everything",
        "service_limit": None,
        "product_limit": None,
        "website_enabled": True,
        "pro_badge": True,
        "featured": True,
        "open_now_priority": 0,
        "directory_rank": 0,
        "featured_services_limit": 6,
        "custom_hero": True,
        "show_map_embed": True,
        "show_testimonial": True,
        "show_public_email": True,
        "show_share_tools": True,
        "show_similar_businesses": True,
        "hide_platform_branding": True,
        "card_style": "featured",
        "features": [
            "Everything in Pro",
            "Unlimited services & products",
            "Featured badge in directory",
            "Highest ranking in search & Open now",
            "6 featured service highlights",
            "Premium featured card styling",
            "Remove SuratBazar branding on booking pages",
        ],
        "not_included": [],
    },
}

PLAN_COMPARE_ROWS = [
    ("Yearly price", "₹0", "₹999/yr", "₹3,999/yr"),
    ("Best for", "New listings", "Growing shops", "Category leaders"),
    ("Bookable services", "Up to 5", "Up to 25", "Unlimited"),
    ("Product listings", "—", "Up to 15", "Unlimited"),
    ("Website button", "—", "✓", "✓"),
    ("Custom hero image", "✓", "✓", "✓"),
    ("Map embed", "—", "✓", "✓"),
    ("Customer testimonial", "—", "✓", "✓"),
    ("Public email on listing", "—", "✓", "✓"),
    ("Share / copy link tools", "—", "✓", "✓"),
    ("Featured services shown", "1", "3", "6"),
    ("Pro badge", "—", "✓", "✓"),
    ("Featured in directory", "—", "—", "✓"),
    ("Search / Open now priority", "Standard", "Higher", "Highest"),
    ("Highlighted directory card", "—", "✓", "Premium style"),
    ("Remove platform branding", "—", "—", "✓"),
    ("Public listing + booking", "✓", "✓", "✓"),
    ("Phone, WhatsApp, directions", "✓", "✓", "✓"),
    ("Hours & Open now", "✓", "✓", "✓"),
]


def get_plan_config(plan_key):
    return PLAN_CONFIG.get(plan_key or "free", PLAN_CONFIG["free"])


def plan_allows_website(plan_key):
    return bool(get_plan_config(plan_key)["website_enabled"])


def plan_product_limit(plan_key):
    return get_plan_config(plan_key)["product_limit"]


def plan_allows_products(plan_key):
    limit = plan_product_limit(plan_key)
    return limit is None or limit > 0


def plan_service_limit(plan_key):
    return get_plan_config(plan_key)["service_limit"]


def plan_is_featured(plan_key):
    return bool(get_plan_config(plan_key)["featured"])


def plan_has_pro_badge(plan_key):
    return bool(get_plan_config(plan_key)["pro_badge"])


def plan_directory_rank(plan_key):
    return get_plan_config(plan_key).get("directory_rank", 2)


def plan_open_now_priority(plan_key):
    return get_plan_config(plan_key).get("open_now_priority", 2)


def plan_featured_services_limit(plan_key):
    return get_plan_config(plan_key).get("featured_services_limit", 1)


def plan_allows_custom_hero(plan_key):
    return bool(get_plan_config(plan_key).get("custom_hero"))


def plan_shows_map_embed(plan_key):
    return bool(get_plan_config(plan_key).get("show_map_embed"))


def plan_shows_testimonial(plan_key):
    return bool(get_plan_config(plan_key).get("show_testimonial"))


def plan_shows_public_email(plan_key):
    return bool(get_plan_config(plan_key).get("show_public_email"))


def plan_shows_share_tools(plan_key):
    return bool(get_plan_config(plan_key).get("show_share_tools"))


def plan_shows_similar_businesses(plan_key):
    return bool(get_plan_config(plan_key).get("show_similar_businesses"))


def plan_hides_platform_branding(plan_key):
    return bool(get_plan_config(plan_key).get("hide_platform_branding"))


def plan_card_style(plan_key):
    return get_plan_config(plan_key).get("card_style", "standard")


def remaining_product_slots(business):
    from catalog.models import Product

    limit = plan_product_limit(business.listing_plan)
    if limit is None:
        return None
    used = Product.objects.filter(business=business, is_active=True).count()
    return max(limit - used, 0)


def can_add_product(business):
    if not plan_allows_products(business.listing_plan):
        return False
    remaining = remaining_product_slots(business)
    return remaining is None or remaining > 0


def remaining_service_slots(business):
    from catalog.models import Service

    limit = plan_service_limit(business.listing_plan)
    if limit is None:
        return None
    used = Service.objects.filter(category__business=business, is_active=True).count()
    return max(limit - used, 0)


def can_add_service(business):
    remaining = remaining_service_slots(business)
    return remaining is None or remaining > 0
