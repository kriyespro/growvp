from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import BusinessHours, Product, Service, ServiceCategory
from catalog.services import DEFAULT_CATEGORIES_BY_INDUSTRY
from users.models import Business, User, UserProfile


# 20 ready-to-list Surat businesses for the public directory.
SEED_BUSINESSES = [
    {
        "name": "Aura Glow Salon",
        "industry_type": "salon",
        "hero_title": "Hair, skin & bridal beauty",
        "hero_subtitle": "Walk in or book online for trusted salon care on Ring Road.",
        "public_phone": "9876500001",
        "public_email": "hello@auraglow.test",
        "public_address": "Shop 12, Ring Road, Surat",
        "testimonial_quote": "Best haircut experience in the area.",
        "testimonial_author": "Neha P.",
        "services": [
            ("Haircut", "Hair", 30, "399"),
            ("Hair Spa", "Hair", 60, "799"),
            ("Facial Glow", "Skin", 45, "999"),
        ],
    },
    {
        "name": "Velvet Scissors Studio",
        "industry_type": "salon",
        "hero_title": "Premium cuts & styling",
        "hero_subtitle": "Modern salon for men’s and women’s grooming.",
        "public_phone": "9876500002",
        "public_email": "book@velvetscissors.test",
        "public_address": "Adajan Gam, Surat",
        "testimonial_quote": "Clean studio and on-time appointments.",
        "testimonial_author": "Raj S.",
        "services": [
            ("Men's Cut", "Hair", 25, "299"),
            ("Beard Trim", "Hair", 15, "149"),
            ("Keratin Care", "Hair", 90, "2499"),
        ],
    },
    {
        "name": "Bliss Nail Parlour",
        "industry_type": "salon",
        "hero_title": "Nails & spa packages",
        "hero_subtitle": "Gel, manicure, pedicure and evening packages.",
        "public_phone": "9876500003",
        "public_email": "care@blissnail.test",
        "public_address": "Vesu Main Road, Surat",
        "testimonial_quote": "Beautiful gel polish every time.",
        "testimonial_author": "Priya J.",
        "services": [
            ("Gel Manicure", "Nails", 40, "699"),
            ("Pedicure", "Nails", 45, "799"),
            ("Spa Package", "Spa", 75, "1499"),
        ],
    },
    {
        "name": "Lumina Bridal Studio",
        "industry_type": "salon",
        "hero_title": "Bridal makeup & pre-wedding prep",
        "hero_subtitle": "Trials, HD makeup and occasion styling.",
        "public_phone": "9876500004",
        "public_email": "bridal@lumina.test",
        "public_address": "Palanpur Gam, Surat",
        "testimonial_quote": "Looked flawless on my wedding day.",
        "testimonial_author": "Sneha T.",
        "services": [
            ("Bridal Makeup", "Skin", 120, "7999"),
            ("Makeup Trial", "Skin", 60, "1999"),
            ("Hair Styling", "Hair", 45, "1499"),
        ],
    },
    {
        "name": "SmileCare Dental Clinic",
        "industry_type": "dentist",
        "hero_title": "Family dentistry in Surat",
        "hero_subtitle": "Cleaning, consultation and painless procedures.",
        "public_phone": "9876500005",
        "public_email": "appointments@smilecare.test",
        "public_address": "Ghod Dod Road, Surat",
        "testimonial_quote": "Gentle dentist and clear pricing.",
        "testimonial_author": "Aarav M.",
        "services": [
            ("Dental Consultation", "Consultation", 20, "299"),
            ("Teeth Cleaning", "Cleaning", 40, "999"),
            ("Whitening", "Whitening", 60, "4999"),
        ],
    },
    {
        "name": "Pearl Orthodontics",
        "industry_type": "dentist",
        "hero_title": "Braces & smile correction",
        "hero_subtitle": "Ortho consults and aligner follow-ups.",
        "public_phone": "9876500006",
        "public_email": "hello@pearortho.test",
        "public_address": "City Light Road, Surat",
        "testimonial_quote": "Professional brace treatment plan.",
        "testimonial_author": "Kiran D.",
        "services": [
            ("Ortho Consultation", "Consultation", 30, "499"),
            ("Braces Review", "Braces", 25, "799"),
            ("Follow-up Visit", "Follow-up", 15, "399"),
        ],
    },
    {
        "name": "WhiteNest Dental",
        "industry_type": "dentist",
        "hero_title": "Routine & emergency dental care",
        "hero_subtitle": "Same-day slots for cleaning and consults.",
        "public_phone": "9876500007",
        "public_email": "desk@whitenest.test",
        "public_address": "Althan BRC, Surat",
        "testimonial_quote": "Fast booking and caring staff.",
        "testimonial_author": "Mehul V.",
        "services": [
            ("Checkup", "Consultation", 20, "249"),
            ("Scaling", "Cleaning", 45, "1199"),
            ("Sensitive Care", "Follow-up", 30, "699"),
        ],
    },
    {
        "name": "ClearVision Opticals",
        "industry_type": "optical",
        "hero_title": "Eye tests & frame studio",
        "hero_subtitle": "Computer eye exams and lens fittings.",
        "public_phone": "9876500008",
        "public_email": "store@clearvision.test",
        "public_address": "Piplod Circle, Surat",
        "testimonial_quote": "Great frame options and quick lenses.",
        "testimonial_author": "Ankit R.",
        "services": [
            ("Eye Test", "Eye Test", 20, "199"),
            ("Frame Fitting", "Frames", 15, "99"),
            ("Lens Upgrade", "Lenses", 30, "1499"),
        ],
    },
    {
        "name": "LensBox Eyewear",
        "industry_type": "optical",
        "hero_title": "Spectacles & contact lenses",
        "hero_subtitle": "Budget to premium frames with repairs.",
        "public_phone": "9876500009",
        "public_email": "help@lensbox.test",
        "public_address": "Varachha Main Road, Surat",
        "testimonial_quote": "Affordable and helpful guidance.",
        "testimonial_author": "Bhavna K.",
        "services": [
            ("Vision Screening", "Eye Test", 15, "149"),
            ("Frame Consultation", "Frames", 20, "0"),
            ("Spectacle Repair", "Repairs", 25, "299"),
        ],
    },
    {
        "name": "FocusPoint Optics",
        "industry_type": "optical",
        "hero_title": "Precision lenses for work & study",
        "hero_subtitle": "Blue-cut lenses and progressive fittings.",
        "public_phone": "9876500010",
        "public_email": "book@focuspoint.test",
        "public_address": "Udhna Magdalla Road, Surat",
        "testimonial_quote": "My blue-cut lenses reduced eye strain.",
        "testimonial_author": "Divya S.",
        "services": [
            ("Eye Exam", "Eye Test", 25, "249"),
            ("Progressive Lens Fitting", "Lenses", 40, "2999"),
            ("Consultation", "Consultation", 15, "99"),
        ],
    },
    {
        "name": "PawPalace Pet Clinic",
        "industry_type": "pet",
        "hero_title": "Vet care & pet wellness",
        "hero_subtitle": "Vaccinations, checkups and grooming.",
        "public_phone": "9876500011",
        "public_email": "clinic@pawpalace.test",
        "public_address": "Athwa Lines, Surat",
        "testimonial_quote": "Our dog loves the gentle team.",
        "testimonial_author": "Rohit C.",
        "services": [
            ("Health Check", "Health Check", 30, "499"),
            ("Vaccination", "Vaccination", 20, "799"),
            ("Full Groom", "Grooming", 60, "999"),
        ],
    },
    {
        "name": "HappyTails Grooming",
        "industry_type": "pet",
        "hero_title": "Bathing & spa for pets",
        "hero_subtitle": "Hygiene packages for dogs and cats.",
        "public_phone": "9876500012",
        "public_email": "book@happytails.test",
        "public_address": "Parle Point, Surat",
        "testimonial_quote": "Clean groom and soft coat every visit.",
        "testimonial_author": "Isha N.",
        "services": [
            ("Bath & Dry", "Bathing", 40, "599"),
            ("Nail Trim", "Grooming", 15, "199"),
            ("Puppy Spa", "Grooming", 50, "899"),
        ],
    },
    {
        "name": "VetNest Animal Care",
        "industry_type": "pet",
        "hero_title": "Clinical pet visits",
        "hero_subtitle": "Vaccines, consults and follow-ups.",
        "public_phone": "9876500013",
        "public_email": "care@vetnest.test",
        "public_address": "Dumbhal, Surat",
        "testimonial_quote": "Clear advice and fair fees.",
        "testimonial_author": "Suresh P.",
        "services": [
            ("Vet Consultation", "Health Check", 25, "399"),
            ("Booster Shot", "Vaccination", 15, "699"),
            ("Training Intro", "Training", 45, "1199"),
        ],
    },
    {
        "name": "Zen Wellness Studio",
        "industry_type": "other",
        "hero_title": "Massage & recovery sessions",
        "hero_subtitle": "Relaxation packages for busy professionals.",
        "public_phone": "9876500014",
        "public_email": "relax@zenwellness.test",
        "public_address": "Surat VIP Road, Surat",
        "testimonial_quote": "Stress melts away here.",
        "testimonial_author": "Kavya L.",
        "services": [
            ("Swedish Massage", "Core Service", 60, "1499"),
            ("Consultation", "Consultation", 20, "299"),
            ("Detox Package", "Packages", 90, "2499"),
        ],
    },
    {
        "name": "FitFirst Physio Hub",
        "industry_type": "other",
        "hero_title": "Physio & pain relief",
        "hero_subtitle": "Sports injury and posture correction.",
        "public_phone": "9876500015",
        "public_email": "clinic@fitfirst.test",
        "public_address": "Katargam, Surat",
        "testimonial_quote": "Knee pain improved in weeks.",
        "testimonial_author": "Nitin G.",
        "services": [
            ("Physio Assessment", "Consultation", 30, "499"),
            ("Therapy Session", "Core Service", 45, "799"),
            ("Follow-up", "Follow-up", 20, "399"),
        ],
    },
    {
        "name": "Bloom Skin Lab",
        "industry_type": "salon",
        "hero_title": "Advanced facials & skin care",
        "hero_subtitle": "Dermat-safe facials with booking slots.",
        "public_phone": "9876500016",
        "public_email": "skin@bloomlab.test",
        "public_address": "Nanpura, Surat",
        "testimonial_quote": "Skin felt fresh and calm.",
        "testimonial_author": "Reena M.",
        "services": [
            ("Cleanup", "Skin", 40, "899"),
            ("Hydra Facial", "Skin", 60, "2499"),
            ("Skin Package", "Packages", 90, "3999"),
        ],
    },
    {
        "name": "KidSmile Pediatric Dental",
        "industry_type": "dentist",
        "hero_title": "Gentle dental care for kids",
        "hero_subtitle": "Fun clinic with child-friendly dentists.",
        "public_phone": "9876500017",
        "public_email": "kids@kidsmile.test",
        "public_address": "Vesu Lakeview, Surat",
        "testimonial_quote": "My son wasn’t scared at all.",
        "testimonial_author": "Pooja H.",
        "services": [
            ("Kids Consultation", "Consultation", 20, "349"),
            ("Kids Cleaning", "Cleaning", 30, "799"),
            ("Fluoride Care", "Follow-up", 20, "499"),
        ],
    },
    {
        "name": "Urban Specs Gallery",
        "industry_type": "optical",
        "hero_title": "Designer frames & express lenses",
        "hero_subtitle": "Style consults with prescription support.",
        "public_phone": "9876500018",
        "public_email": "gallery@urbanspecs.test",
        "public_address": "VR Mall Road, Surat",
        "testimonial_quote": "Found frames I actually love.",
        "testimonial_author": "Harsh T.",
        "services": [
            ("Style Consultation", "Consultation", 20, "0"),
            ("Eye Test", "Eye Test", 20, "199"),
            ("Express Lenses", "Lenses", 45, "1999"),
        ],
    },
    {
        "name": "Meadow Pet Boutique Clinic",
        "industry_type": "pet",
        "hero_title": "Grooming + basic vet services",
        "hero_subtitle": "Boutique pet care near VIP Road.",
        "public_phone": "9876500019",
        "public_email": "meadow@petboutique.test",
        "public_address": "Pal Village, Surat",
        "testimonial_quote": "Stylish groom and healthy tips.",
        "testimonial_author": "Ayesha F.",
        "services": [
            ("Boutique Groom", "Grooming", 55, "1299"),
            ("Health Check", "Health Check", 25, "449"),
            ("Bath Deluxe", "Bathing", 45, "749"),
        ],
    },
    {
        "name": "Nightingale Voice & Speech",
        "industry_type": "other",
        "hero_title": "Speech therapy consultations",
        "hero_subtitle": "Sessions for kids and adults by appointment.",
        "public_phone": "9876500020",
        "public_email": "book@nightingale.test",
        "public_address": "Rander Road, Surat",
        "testimonial_quote": "Clear progress after a few sessions.",
        "testimonial_author": "Farhan A.",
        "services": [
            ("Initial Assessment", "Consultation", 40, "999"),
            ("Therapy Session", "Core Service", 45, "1299"),
            ("Parent Guidance", "Add-ons", 30, "699"),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed 20 complete public business listings for the directory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously seeded directory businesses (seed_* emails) before creating.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset_seeded()

        created_count = 0
        updated_count = 0
        for index, spec in enumerate(SEED_BUSINESSES, start=1):
            business, created = self._upsert_business(spec, index)
            self._ensure_admin(business, index)
            self._ensure_categories_and_services(business, spec)
            self._ensure_hours(business)
            self._ensure_plan_and_products(business, index)
            if created:
                created_count += 1
            else:
                updated_count += 1
            self.stdout.write(
                f"{'Created' if created else 'Updated'}: {business.name} (/b/{business.slug}/) [{business.listing_plan}]"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded 20 directory businesses ({created_count} created, {updated_count} updated)."
            )
        )
        self.stdout.write("Sample admin login: seed01.admin@test.com / test1234")

    def _reset_seeded(self):
        users = User.objects.filter(email__startswith="seed")
        businesses = Business.objects.filter(staff__user__in=users).distinct()
        deleted_b, _ = businesses.delete()
        deleted_u, _ = users.delete()
        self.stdout.write(f"Reset removed businesses/users batch (business ops={deleted_b}, users={deleted_u}).")

    def _upsert_business(self, spec, index):
        # Rotate Free / Pro / Premium across seed listings for directory demos.
        plan = ("free", "pro", "premium")[(index - 1) % 3]
        website = ""
        if plan in ("pro", "premium"):
            website = f"https://example-{index:02d}.suratbazar.test"

        slug = slugify(spec["name"])
        business, created = Business.objects.update_or_create(
            slug=slug,
            defaults={
                "name": spec["name"],
                "industry_type": spec["industry_type"],
                "timezone": "Asia/Kolkata",
                "hero_title": spec["hero_title"],
                "hero_subtitle": spec["hero_subtitle"],
                "public_phone": spec["public_phone"],
                "public_email": spec["public_email"],
                "public_address": spec["public_address"],
                "website_url": website,
                "listing_plan": plan,
                "testimonial_quote": spec.get("testimonial_quote", ""),
                "testimonial_author": spec.get("testimonial_author", ""),
                "profile_setup_completed": True,
                "upi_id": f"seed{index:02d}@upi",
            },
        )
        return business, created

    def _ensure_admin(self, business, index):
        email = f"seed{index:02d}.admin@test.com"
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": "Seed",
                "last_name": f"Admin{index:02d}",
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

    def _ensure_categories_and_services(self, business, spec):
        category_names = DEFAULT_CATEGORIES_BY_INDUSTRY.get(
            business.industry_type,
            DEFAULT_CATEGORIES_BY_INDUSTRY["other"],
        )
        categories = {}
        for name in category_names:
            category, _ = ServiceCategory.objects.get_or_create(
                business=business,
                name=name,
            )
            categories[name] = category

        for service_name, category_name, duration, price in spec["services"]:
            category = categories.get(category_name) or next(iter(categories.values()))
            Service.objects.update_or_create(
                category=category,
                name=service_name,
                defaults={
                    "description": f"{service_name} at {business.name}.",
                    "duration_mins": duration,
                    "price": Decimal(price),
                    "is_active": True,
                },
            )

    def _ensure_hours(self, business):
        for day in range(7):
            is_closed = day == 6  # Sunday closed
            BusinessHours.objects.update_or_create(
                business=business,
                day_of_week=day,
                defaults={
                    "is_closed": is_closed,
                    "start_time": None if is_closed else time(10, 0),
                    "end_time": None if is_closed else time(19, 0),
                },
            )

    def _ensure_plan_and_products(self, business, index):
        if business.listing_plan == "free":
            # Free ladder: services only — no products
            Product.objects.filter(business=business).delete()
            return

        samples = [
            ("Signature Care Kit", "In-store aftercare kit.", "499"),
            ("Travel Pack", "Compact take-home pack.", "299"),
            ("Membership Card", "Loyalty punch card.", "199"),
        ]
        count = 3 if business.listing_plan == "premium" else 2
        for name, description, price in samples[:count]:
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
