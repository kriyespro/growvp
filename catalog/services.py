from datetime import time

from .models import ServiceCategory, BusinessHours, Service


DEFAULT_CATEGORIES_BY_INDUSTRY = {
    "salon": ["Hair", "Skin", "Nails", "Spa", "Packages"],
    "spa": ["Massage", "Facial", "Body Care", "Packages", "Add-ons"],
    "grooming": ["Haircut", "Beard", "Styling", "Packages", "Add-ons"],
    "dentist": ["Consultation", "Cleaning", "Whitening", "Braces", "Follow-up"],
    "clinic": ["Consultation", "Check-up", "Lab Tests", "Treatment", "Follow-up"],
    "optical": ["Eye Test", "Frames", "Lenses", "Repairs", "Consultation"],
    "physiotherapy": ["Assessment", "Session", "Rehab", "Sports Care", "Packages"],
    "ayurveda": ["Consultation", "Therapy", "Panchakarma", "Wellness", "Products"],
    "gym": ["Membership", "Personal Training", "Classes", "Assessment", "Add-ons"],
    "yoga": ["Drop-in Class", "Monthly Pass", "Private Session", "Workshop", "Packages"],
    "restaurant": ["Dine-in", "Takeaway", "Catering", "Specials", "Events"],
    "bakery": ["Cakes", "Snacks", "Custom Orders", "Bulk Orders", "Seasonal"],
    "grocery": ["Daily Essentials", "Fresh Produce", "Home Delivery", "Bulk", "Specials"],
    "fashion": ["Men's Wear", "Women's Wear", "Alterations", "Accessories", "Custom"],
    "pet": ["Grooming", "Bathing", "Health Check", "Vaccination", "Training"],
    "auto": ["Service", "Repair", "Inspection", "Detailing", "Parts"],
    "laundry": ["Wash & Iron", "Dry Clean", "Express", "Bulk", "Pickup"],
    "tailoring": ["Stitching", "Alterations", "Custom Fit", "Embroidery", "Repairs"],
    "home_services": ["Plumbing", "Electrical", "Cleaning", "AC Service", "Repairs"],
    "photography": ["Portrait", "Event", "Product", "Editing", "Packages"],
    "coaching": ["Trial Class", "Monthly Plan", "Crash Course", "1-on-1", "Group"],
    "events": ["Planning", "Decoration", "Catering Tie-up", "Venue", "Packages"],
    "legal": ["Consultation", "Documentation", "Filing", "Advisory", "Packages"],
    "realestate": ["Site Visit", "Consultation", "Listing", "Rental", "Documentation"],
    "other": ["Consultation", "Core Service", "Add-ons", "Packages", "Follow-up"],
}


def ensure_starter_categories(business):
    category_names = DEFAULT_CATEGORIES_BY_INDUSTRY.get(
        business.industry_type,
        DEFAULT_CATEGORIES_BY_INDUSTRY["other"],
    )

    for name in category_names:
        ServiceCategory.objects.get_or_create(
            business=business,
            name=name,
        )


DEFAULT_OPEN_DAYS = {0, 1, 2, 3, 4, 5}  # Mon–Sat
DEFAULT_START = time(10, 0)
DEFAULT_END = time(19, 0)


def ensure_default_hours(business):
    """Seed weekly hours once so Open now can work after onboarding."""
    if BusinessHours.objects.filter(business=business).exists():
        return list(BusinessHours.objects.filter(business=business).order_by("day_of_week"))

    created = []
    for day in range(7):
        is_closed = day not in DEFAULT_OPEN_DAYS
        row = BusinessHours.objects.create(
            business=business,
            day_of_week=day,
            start_time=None if is_closed else DEFAULT_START,
            end_time=None if is_closed else DEFAULT_END,
            is_closed=is_closed,
        )
        created.append(row)
    return created


def get_business_hours(business):
    ensure_default_hours(business)
    return list(BusinessHours.objects.filter(business=business).order_by("day_of_week"))


def update_business_hours_from_post(business, post_data):
    """Update Mon–Sun hours from onboarding/dashboard POST fields."""
    ensure_default_hours(business)
    updated = []
    for day in range(7):
        row = BusinessHours.objects.get(business=business, day_of_week=day)
        is_closed = post_data.get(f"day_{day}_closed") == "1"
        start_raw = (post_data.get(f"day_{day}_start") or "").strip()
        end_raw = (post_data.get(f"day_{day}_end") or "").strip()

        row.is_closed = is_closed
        if is_closed:
            row.start_time = None
            row.end_time = None
        else:
            try:
                row.start_time = time.fromisoformat(start_raw) if start_raw else DEFAULT_START
                row.end_time = time.fromisoformat(end_raw) if end_raw else DEFAULT_END
            except ValueError:
                row.start_time = DEFAULT_START
                row.end_time = DEFAULT_END
            if row.start_time and row.end_time and row.start_time >= row.end_time:
                # Keep a sane window if overnight not supported in UI
                row.end_time = DEFAULT_END
        row.save()
        updated.append(row)
    return updated


def get_listing_readiness(business):
    """Checklist progress for onboarding / dashboard."""
    service_count = Service.objects.filter(
        category__business=business, is_active=True
    ).count()
    hours_count = BusinessHours.objects.filter(business=business, is_closed=False).count()
    has_phone = bool((business.public_phone or "").strip())
    has_address = bool((business.public_address or "").strip())
    has_hero = bool((business.hero_title or "").strip() or (business.hero_image_url or "").strip())
    has_services = service_count > 0
    has_hours = hours_count > 0

    steps = [
        {"key": "phone", "label": "Add public phone", "done": has_phone},
        {"key": "address", "label": "Add business address", "done": has_address},
        {"key": "hours", "label": "Set opening hours", "done": has_hours},
        {"key": "services", "label": "Add at least one bookable service", "done": has_services},
        {"key": "hero", "label": "Add hero title or image (optional)", "done": has_hero, "optional": True},
    ]
    required = [s for s in steps if not s.get("optional")]
    done_required = sum(1 for s in required if s["done"])
    return {
        "steps": steps,
        "done_required": done_required,
        "total_required": len(required),
        "percent": int((done_required / len(required)) * 100) if required else 100,
        "is_bookable": has_services,
        "is_complete": done_required == len(required),
    }
