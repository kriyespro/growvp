"""
Seed N realistic Surat directory listings (default 200).

  ./venv/bin/python manage.py seed_bulk_directory
  ./venv/bin/python manage.py seed_bulk_directory --count 200
  ./venv/bin/python manage.py seed_bulk_directory --count 200 --reset

Logins: bulk001.admin@test.com … bulk200.admin@test.com / test1234
"""

from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import BusinessHours, Product, Service, ServiceCategory
from catalog.services import DEFAULT_CATEGORIES_BY_INDUSTRY
from users.industries import industry_choices_flat
from users.models import Business, User, UserProfile


SURAT_AREAS = [
    "Adajan",
    "Vesu",
    "Piplod",
    "City Light",
    "Athwa",
    "Ghod Dod Road",
    "Ring Road",
    "Varachha",
    "Katargam",
    "Pal",
    "Palanpur",
    "Althan",
    "Udhna",
    "Sachin",
    "Dumas Road",
    "LP Savani Road",
    "VIP Road",
    "Nanpura",
    "Majura Gate",
    "Sarthana",
    "Kamrej",
    "Rander",
    "Amroli",
    "Mota Varachha",
]

NAME_PREFIX = [
    "Royal",
    "Prime",
    "Urban",
    "Green",
    "Golden",
    "Silver",
    "Pearl",
    "Crown",
    "Bright",
    "Lotus",
    "Shree",
    "Om",
    "Nova",
    "Aarohi",
    "Sundaram",
    "Harmony",
    "Elite",
    "Metro",
    "Vista",
    "Anchor",
    "Beacon",
    "Coral",
    "Amber",
    "Cedar",
    "Maple",
]

NAME_SUFFIX = {
    "salon": ["Salon", "Parlour", "Beauty Studio", "Glow Studio"],
    "spa": ["Spa", "Wellness Centre", "Therapy Spa"],
    "grooming": ["Barbershop", "Gents Grooming", "Cuts Studio"],
    "dentist": ["Dental Clinic", "Dental Care", "Smiles Clinic"],
    "clinic": ["Clinic", "Polyclinic", "Family Clinic"],
    "optical": ["Opticals", "Eye Care", "Vision Hub"],
    "physiotherapy": ["Physio Hub", "Rehab Centre", "Physiotherapy"],
    "ayurveda": ["Ayurveda Centre", "Panchakarma", "Herbal Clinic"],
    "gym": ["Fitness", "Gym", "Training Club"],
    "yoga": ["Yoga Studio", "Yoga Centre", "Pilates Studio"],
    "restaurant": ["Kitchen", "Cafe", "Bistro", "Tandoor"],
    "bakery": ["Bakery", "Sweet House", "Bake Lab"],
    "grocery": ["Kirana", "Fresh Mart", "Grocery"],
    "fashion": ["Boutique", "Fashion Hub", "Apparel"],
    "pet": ["Pet Clinic", "Pet Care", "Paw Centre"],
    "auto": ["Auto Care", "Garage", "Service Point"],
    "laundry": ["Laundry", "Dry Clean", "Wash Hub"],
    "tailoring": ["Tailors", "Stitch Studio", "Alterations"],
    "home_services": ["Home Care", "Services", "Fixit Hub"],
    "photography": ["Studio", "Photography", "Frames"],
    "coaching": ["Academy", "Tuition Centre", "Coaching"],
    "events": ["Events", "Wedding Desk", "Celebrations"],
    "legal": ["Associates", "Consultants", "Advisors"],
    "realestate": ["Realtors", "Properties", "Homes"],
    "other": ["Centre", "Point", "Services"],
}

SERVICE_TEMPLATES = {
    "salon": [("Haircut", 30, "349"), ("Hair Spa", 60, "799"), ("Facial", 45, "999")],
    "spa": [("Relax Massage", 45, "1299"), ("Body Scrub", 40, "999"), ("Aroma Therapy", 50, "1499")],
    "grooming": [("Men's Cut", 25, "249"), ("Beard Trim", 15, "149"), ("Hair Colour", 45, "799")],
    "dentist": [("Consultation", 20, "299"), ("Cleaning", 40, "999"), ("Filling", 45, "1499")],
    "clinic": [("General Checkup", 20, "399"), ("Follow-up", 15, "249"), ("Health Package", 40, "1999")],
    "optical": [("Eye Test", 20, "199"), ("Frame Fitting", 25, "0"), ("Lens Consult", 20, "299")],
    "physiotherapy": [("Assessment", 30, "499"), ("Therapy Session", 45, "799"), ("Rehab Plan", 40, "1299")],
    "ayurveda": [("Consult", 25, "399"), ("Therapy", 45, "1299"), ("Detox Session", 60, "2499")],
    "gym": [("Day Pass", 60, "199"), ("PT Session", 45, "699"), ("Monthly Plan", 30, "1499")],
    "yoga": [("Group Class", 60, "299"), ("Private Session", 45, "799"), ("Beginner Intro", 40, "399")],
    "restaurant": [("Table Booking", 60, "0"), ("Thali", 45, "249"), ("Family Meal", 60, "799")],
    "bakery": [("Cake Order", 30, "599"), ("Custom Design", 45, "1299"), ("Snack Box", 20, "299")],
    "grocery": [("Home Delivery", 30, "49"), ("Bulk Order", 40, "0"), ("Monthly Basket", 30, "999")],
    "fashion": [("Alteration", 30, "199"), ("Styling Consult", 40, "499"), ("Custom Order", 45, "1499")],
    "pet": [("Checkup", 25, "399"), ("Vaccination", 20, "699"), ("Grooming", 45, "899")],
    "auto": [("Service", 60, "999"), ("Oil Change", 40, "699"), ("Diagnostics", 30, "499")],
    "laundry": [("Wash & Fold", 24, "149"), ("Dry Clean", 48, "249"), ("Express", 12, "299")],
    "tailoring": [("Alteration", 30, "199"), ("Blouse Stitch", 90, "799"), ("Suit Stitch", 120, "2499")],
    "home_services": [("Visit Charge", 40, "299"), ("Repair Job", 60, "799"), ("Deep Clean", 120, "1999")],
    "photography": [("Portrait", 45, "1499"), ("Event Coverage", 180, "7999"), ("Product Shoot", 60, "2499")],
    "coaching": [("Demo Class", 45, "0"), ("Monthly Batch", 60, "2499"), ("Doubt Session", 30, "399")],
    "events": [("Planning Consult", 40, "999"), ("Decor Package", 120, "14999"), ("Host Assist", 60, "2999")],
    "legal": [("Consult", 30, "999"), ("Document Review", 45, "1499"), ("Filing Help", 60, "2999")],
    "realestate": [("Site Visit", 60, "0"), ("Listing Consult", 40, "999"), ("Rental Assist", 45, "1499")],
    "other": [("Consultation", 30, "399"), ("Standard Service", 45, "799"), ("Premium Package", 60, "1499")],
}


class Command(BaseCommand):
    help = "Seed many realistic Surat directory businesses (default 200)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=200,
            help="Number of businesses to create (default 200).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previous bulk* seeded users/businesses first.",
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=1,
            help="Start index for bulkNNN emails/slugs (default 1).",
        )

    def handle(self, *args, **options):
        count = max(1, min(int(options["count"]), 2000))
        offset = max(1, int(options["offset"]))
        if options["reset"]:
            self._reset_bulk()

        industries = [key for key, _ in industry_choices_flat() if key != "other"]
        if not industries:
            industries = ["salon"]

        created = updated = 0
        for i in range(count):
            index = offset + i
            industry = industries[(index - 1) % len(industries)]
            area = SURAT_AREAS[(index - 1) % len(SURAT_AREAS)]
            prefix = NAME_PREFIX[(index - 1) % len(NAME_PREFIX)]
            suffixes = NAME_SUFFIX.get(industry, NAME_SUFFIX["other"])
            suffix = suffixes[(index - 1) % len(suffixes)]
            name = f"{prefix} {suffix} {area}"
            # Avoid exact name collisions across large runs
            if Business.objects.filter(name=name).exclude(slug__startswith=f"bulk-{index:03d}").exists():
                name = f"{prefix} {suffix} {area} #{index}"

            plan = ("free", "pro", "premium")[(index - 1) % 3]
            phone = f"98{(70000000 + index) % 100000000:08d}"
            email = f"hello{index:03d}@{slugify(prefix)}{index}.test"
            slug = f"bulk-{index:03d}-{slugify(industry)[:12]}"
            website = (
                f"https://{slug}.example.test" if plan in ("pro", "premium") else ""
            )

            business, was_created = Business.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "industry_type": industry,
                    "timezone": "Asia/Kolkata",
                    "hero_title": f"{name} in {area}",
                    "hero_subtitle": (
                        f"Book trusted {industry.replace('_', ' ')} services near {area}, Surat."
                    ),
                    "public_phone": phone,
                    "public_email": email,
                    "public_address": f"Near Main Road, {area}, Surat",
                    "website_url": website,
                    "listing_plan": plan,
                    "testimonial_quote": (
                        "Reliable service and fair pricing."
                        if plan != "free"
                        else ""
                    ),
                    "testimonial_author": "Local customer" if plan != "free" else "",
                    "map_embed_url": (
                        "https://maps.google.com/?q=Surat+" + slugify(area)
                        if plan == "premium"
                        else ""
                    ),
                    "profile_setup_completed": True,
                    "upi_id": f"bulk{index:03d}@upi",
                },
            )
            self._ensure_admin(business, index)
            self._ensure_services(business, industry)
            self._ensure_hours(business, index)
            self._ensure_products(business)

            if was_created:
                created += 1
            else:
                updated += 1

            if index % 25 == 0 or i == count - 1:
                self.stdout.write(f"… {i + 1}/{count} ({name})")

        self.stdout.write(
            self.style.SUCCESS(
                f"Bulk seed done: {count} listings ({created} created, {updated} updated)."
            )
        )
        self.stdout.write(
            f"Sample login: bulk{offset:03d}.admin@test.com / test1234"
        )

    def _reset_bulk(self):
        users = User.objects.filter(email__startswith="bulk")
        businesses = Business.objects.filter(
            slug__startswith="bulk-"
        ) | Business.objects.filter(staff__user__in=users)
        businesses = businesses.distinct()
        deleted_b, _ = businesses.delete()
        deleted_u, _ = users.delete()
        self.stdout.write(
            f"Reset bulk seed (business ops={deleted_b}, users={deleted_u})."
        )

    def _ensure_admin(self, business, index):
        email = f"bulk{index:03d}.admin@test.com"
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": "Bulk",
                "last_name": f"{index:03d}",
                "is_active": True,
                "platform_role": "business",
            },
        )
        user.set_password("test1234")
        user.platform_role = "business"
        user.save()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "business": business,
                "role": "admin",
                "phone": business.public_phone,
            },
        )
        if not business.created_by_id:
            business.created_by = user
            business.save(update_fields=["created_by"])

    def _ensure_services(self, business, industry):
        category_names = DEFAULT_CATEGORIES_BY_INDUSTRY.get(
            industry, DEFAULT_CATEGORIES_BY_INDUSTRY["other"]
        )
        categories = {}
        for name in category_names:
            cat, _ = ServiceCategory.objects.get_or_create(
                business=business, name=name
            )
            categories[name] = cat

        templates = SERVICE_TEMPLATES.get(industry, SERVICE_TEMPLATES["other"])
        default_cat = next(iter(categories.values()))
        for service_name, duration, price in templates:
            # Prefer matching category by keyword else first category
            cat = default_cat
            for cname, cobj in categories.items():
                if cname.lower().split()[0] in service_name.lower():
                    cat = cobj
                    break
            Service.objects.update_or_create(
                category=cat,
                name=service_name,
                defaults={
                    "description": f"{service_name} at {business.name}.",
                    "duration_mins": duration,
                    "price": Decimal(price),
                    "is_active": True,
                },
            )

    def _ensure_hours(self, business, index):
        # Vary closing day slightly so “open now” isn’t identical for all
        closed_day = (index - 1) % 7
        open_hour = 9 + (index % 3)
        close_hour = 19 + (index % 2)
        for day in range(7):
            is_closed = day == closed_day
            BusinessHours.objects.update_or_create(
                business=business,
                day_of_week=day,
                defaults={
                    "is_closed": is_closed,
                    "start_time": None if is_closed else time(open_hour, 0),
                    "end_time": None if is_closed else time(close_hour, 0),
                },
            )

    def _ensure_products(self, business):
        if business.listing_plan == "free":
            Product.objects.filter(business=business).delete()
            return
        samples = [
            ("Care Kit", "Aftercare essentials.", "399"),
            ("Membership Card", "Priority booking loyalty card.", "999"),
            ("Starter Bundle", "Popular take-home bundle.", "699"),
        ]
        n = 3 if business.listing_plan == "premium" else 2
        for name, description, price in samples[:n]:
            Product.objects.update_or_create(
                business=business,
                name=name,
                defaults={
                    "description": f"{description} From {business.name}.",
                    "price": Decimal(price),
                    "buy_url": business.website_url or "",
                    "is_active": True,
                },
            )
