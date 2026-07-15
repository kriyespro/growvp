"""Business industry categories for onboarding and directory filters."""

INDUSTRY_GROUPS = [
    (
        "Beauty & wellness",
        [
            ("salon", "Salon / Parlour"),
            ("spa", "Spa & Wellness"),
            ("grooming", "Barbershop / Grooming"),
        ],
    ),
    (
        "Health & medical",
        [
            ("dentist", "Dentist Clinic"),
            ("clinic", "Clinic / Doctor"),
            ("optical", "Optical Shop"),
            ("physiotherapy", "Physiotherapy"),
            ("ayurveda", "Ayurveda / Homeopathy"),
        ],
    ),
    (
        "Fitness & sports",
        [
            ("gym", "Gym / Fitness Studio"),
            ("yoga", "Yoga / Pilates"),
        ],
    ),
    (
        "Food & retail",
        [
            ("restaurant", "Restaurant / Café"),
            ("bakery", "Bakery / Sweet Shop"),
            ("grocery", "Grocery / Kirana"),
            ("fashion", "Fashion / Boutique"),
        ],
    ),
    (
        "Home & local services",
        [
            ("pet", "Pet Shop / Clinic"),
            ("auto", "Auto Service / Garage"),
            ("laundry", "Laundry / Dry Clean"),
            ("tailoring", "Tailor / Alterations"),
            ("home_services", "Home Services"),
        ],
    ),
    (
        "Professional & events",
        [
            ("photography", "Photography / Studio"),
            ("coaching", "Coaching / Tuition"),
            ("events", "Events / Wedding"),
            ("legal", "Legal / CA / Consultant"),
            ("realestate", "Real Estate"),
        ],
    ),
    (
        "Other",
        [
            ("other", "Other"),
        ],
    ),
]


def industry_choices_flat():
    """Flat (value, label) list for model fields and forms."""
    choices = []
    for _group, items in INDUSTRY_GROUPS:
        choices.extend(items)
    return choices


def industry_label(value):
    mapping = dict(industry_choices_flat())
    return mapping.get(value, "Other")
