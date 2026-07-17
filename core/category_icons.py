"""Industry category SVG icons (Heroicons-style stroke paths, 24×24)."""

from __future__ import annotations

from markupsafe import Markup

from users.industries import INDUSTRY_GROUPS, industry_label

# Short labels for compact home icon strip
HERO_SHORT_LABELS = {
    "salon": "Salon",
    "spa": "Spa",
    "grooming": "Barber",
    "dentist": "Dentist",
    "clinic": "Clinic",
    "optical": "Optical",
    "physiotherapy": "Physio",
    "ayurveda": "Ayurveda",
    "gym": "Gym",
    "yoga": "Yoga",
    "restaurant": "Food",
    "bakery": "Bakery",
    "grocery": "Kirana",
    "fashion": "Fashion",
    "pet": "Pets",
    "auto": "Auto",
    "laundry": "Laundry",
    "tailoring": "Tailor",
    "home_services": "Home",
    "photography": "Photo",
    "coaching": "Tuition",
    "events": "Events",
    "legal": "Legal",
    "realestate": "Property",
    "other": "Other",
}

# Keys shown on home icon strip (curated order)
HERO_CATEGORY_KEYS = (
    "restaurant",  # Food
    "fashion",
    "gym",
    "coaching",  # Tuition
    "optical",
    "salon",
    "spa",
    "grooming",
    "dentist",
    "clinic",
    "pet",
    "photography",
)

# path d= ... for stroke icons (currentColor)
_ICON_PATHS = {
    "salon": "M9 7V5a3 3 0 0 1 6 0v2M7 11h10M8 11l1 10h6l1-10M12 11v10",
    "spa": "M12 3c2 4 2 7 0 10-2-3-2-6 0-10Zm0 10c3 1 5 3 5 6a5 5 0 1 1-10 0c0-3 2-5 5-6Z",
    "grooming": "M6 4h3v16H6V4Zm9 0h3l-2 8h4l-5 8h-3l2-8h-4l5-8Z",
    "dentist": "M8 4c0 0 1-1 4-1s4 1 4 1v5c0 2-1 3-2 5l1 6h-2l-1-5-1 5H9l1-6c-1-2-2-3-2-5V4Z",
    "clinic": "M11 3h2v6h6v2h-6v6h-2v-6H5V9h6V3Zm-7 18h16",
    "optical": "M3 12a4 4 0 1 0 8 0 4 4 0 1 0-8 0Zm10 0a4 4 0 1 0 8 0 4 4 0 1 0-8 0ZM11 12h2",
    "physiotherapy": "M12 4v4M8 21l4-9 4 9M6 12h12M9 8l-2 2m8-2 2 2",
    "ayurveda": "M12 3v3m0 12v3M5 8l2 1m12-1-2 1M5 16l2-1m12 1-2-1M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z",
    "gym": "M4 10h2v4H4v-4Zm14 0h2v4h-2v-4ZM8 9h2v6H8V9Zm6 0h2v6h-2V9Zm-2 2h2v2h-2v-2Z",
    "yoga": "M12 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4ZM8 20l4-7 4 7M6 12h12",
    "restaurant": "M8 3v10a2 2 0 0 0 2 2h0V3M6 3v7M14 3h2v18h-2V8h-2V3h2Z",
    "bakery": "M4 14c0-4 3-7 8-7s8 3 8 7v1H4v-1Zm2 1h12v4H6v-4Z",
    "grocery": "M4 7h16l-1 12H5L4 7Zm4-3h8l1 3H7l1-3Z",
    "fashion": "M8 4l4 3 4-3 3 4-3 2v10H8V10L5 8l3-4Z",
    "pet": "M5.5 9a2 2 0 1 0 0.01 0ZM9 6.5a2 2 0 1 0 0.01 0ZM15 6.5a2 2 0 1 0 0.01 0ZM18.5 9a2 2 0 1 0 0.01 0ZM12 10c-3 0-5 2.2-5 5.5S9.5 20 12 20s5-1.5 5-4.5S15 10 12 10Z",
    "auto": "M3 13l2-5h14l2 5M5 13h14v5H5v-5Zm2 5v2m10-2v2M7 13.5a1 1 0 1 0 0.01 0Zm10 0a1 1 0 1 0 0.01 0Z",
    "laundry": "M8 4h8v3H8V4Zm1 3v13h6V7M10 11h.01M12 14h.01M14 17h.01",
    "tailoring": "M14.5 4L9 14l3 6M9.5 4L15 14l-1.5 3M4 8h4M16 8h4M6 12h2m8 0h2",
    "home_services": "M4 11l8-7 8 7v9H4v-9Zm6 9v-5h4v5",
    "photography": "M4 8h3l2-2h6l2 2h3v12H4V8Zm8 3a3 3 0 1 0 0.01 0Z",
    "coaching": "M4 19V5h10v14H4Zm10-8h6v8h-6m-6-6h4M8 8h4",
    "events": "M8 3v3M16 3v3M4 9h16M6 6h12a2 2 0 0 1 2 2v11H4V8a2 2 0 0 1 2-2Zm3 7h2v2H9v-2Zm5 0h2v2h-2v-2Z",
    "legal": "M12 3v2M5 8h14l-1 12H6L5 8Zm7 4v5m-3 3h6",
    "realestate": "M3 10l9-7 9 7v10H3V10Zm6 10v-5h6v5",
    "other": "M12 6a2 2 0 1 0 0.01 0ZM12 12a2 2 0 1 0 0.01 0ZM12 18a2 2 0 1 0 0.01 0Z",
}


def industry_icon_svg(key: str, *, size_class: str = "h-6 w-6") -> Markup:
    """Return inline SVG markup for an industry key."""
    path = _ICON_PATHS.get(key) or _ICON_PATHS["other"]
    return Markup(
        f'<svg class="{size_class}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true"><path d="{path}"/></svg>'
    )


def hero_category_items():
    """Compact icon strip items for the home hero."""
    items = []
    for key in HERO_CATEGORY_KEYS:
        items.append(
            {
                "key": key,
                "label": HERO_SHORT_LABELS.get(key) or industry_label(key),
                "path": f"/surat/{key}/",
                "icon": industry_icon_svg(key, size_class="h-6 w-6"),
            }
        )
    return items


def footer_category_columns():
    """
    Industry groups as footer columns (4-col friendly).
    Skips empty 'Other' stuffing; always includes links to /surat/<key>/.
    """
    columns = []
    for group_label, items in INDUSTRY_GROUPS:
        if group_label == "Other":
            continue
        columns.append(
            {
                "title": group_label,
                "links": [
                    {
                        "key": key,
                        "label": label,
                        "path": f"/surat/{key}/",
                    }
                    for key, label in items
                ],
            }
        )
    return columns
