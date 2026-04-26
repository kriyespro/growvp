from .models import ServiceCategory


DEFAULT_CATEGORIES_BY_INDUSTRY = {
    "salon": ["Hair", "Skin", "Nails", "Spa", "Packages"],
    "dentist": ["Consultation", "Cleaning", "Whitening", "Braces", "Follow-up"],
    "optical": ["Eye Test", "Frames", "Lenses", "Repairs", "Consultation"],
    "pet": ["Grooming", "Bathing", "Health Check", "Vaccination", "Training"],
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
