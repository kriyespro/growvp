"""
Seed platform roles for QA: super admin, partners, clients, assignments, enquiries.

  ./venv/bin/python manage.py seed_roles
  ./venv/bin/python manage.py seed_roles --reset
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Product, Service, ServiceCategory
from catalog.services import ensure_default_hours, ensure_starter_categories
from leads.models import Enquiry, EnquiryMessage
from users.models import Business, User, UserProfile
from users.services import assign_partner_to_business, create_partner_listing


PASSWORD = "test1234"


class Command(BaseCommand):
    help = "Seed super admin, marketing partners, clients, partner listings, enquiries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete role-seed users (partner*/client*/role.*) and their partner-created listings.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        admin = self._ensure_super_admin()
        partners = self._ensure_partners()
        clients = self._ensure_clients()
        self._backfill_business_users()
        listings = self._ensure_partner_listings(partners)
        self._assign_partners_to_existing(partners)
        enquiries = self._ensure_enquiries(clients, partners, listings)

        self.stdout.write(self.style.SUCCESS("Role seed completed."))
        self.stdout.write("")
        self.stdout.write("Super admin  /admin/   admin@test.com / test1234")
        self.stdout.write("Partner 1    /partner/ partner01@test.com / test1234")
        self.stdout.write("Partner 2    /partner/ partner02@test.com / test1234")
        self.stdout.write("Client 1     /account/ client01@test.com / test1234")
        self.stdout.write("Client 2     /account/ client02@test.com / test1234")
        self.stdout.write("Business     /dashboard/ demo.admin@test.com / test1234")
        self.stdout.write(
            f"Partners={len(partners)} listings={len(listings)} enquiries={enquiries} "
            f"super_admin={admin.email}"
        )

    def _reset(self):
        emails = list(
            User.objects.filter(
                email__in=[
                    "partner01@test.com",
                    "partner02@test.com",
                    "partner03@test.com",
                    "client01@test.com",
                    "client02@test.com",
                    "client03@test.com",
                ]
            ).values_list("id", flat=True)
        )
        # Partner-created listings (no staff profile, or created_by partner)
        Business.objects.filter(created_by_id__in=emails).delete()
        User.objects.filter(id__in=emails).delete()
        self.stdout.write("Reset role-seed partners/clients and partner listings.")

    def _ensure_user(self, email, *, platform_role, first_name, last_name, is_staff=False, is_superuser=False):
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
                "platform_role": platform_role,
                "is_active": True,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        user.set_password(PASSWORD)
        user.platform_role = platform_role
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
        return user

    def _ensure_super_admin(self):
        return self._ensure_user(
            "admin@test.com",
            platform_role="super_admin",
            first_name="Platform",
            last_name="Admin",
            is_staff=True,
            is_superuser=True,
        )

    def _ensure_partners(self):
        specs = [
            ("partner01@test.com", "Riya", "Partner"),
            ("partner02@test.com", "Amit", "Partner"),
            ("partner03@test.com", "Neha", "Partner"),
        ]
        return [
            self._ensure_user(
                email,
                platform_role="marketing_partner",
                first_name=first,
                last_name=last,
            )
            for email, first, last in specs
        ]

    def _ensure_clients(self):
        specs = [
            ("client01@test.com", "Karan", "Client"),
            ("client02@test.com", "Meera", "Client"),
            ("client03@test.com", "Dev", "Client"),
        ]
        return [
            self._ensure_user(
                email,
                platform_role="client",
                first_name=first,
                last_name=last,
            )
            for email, first, last in specs
        ]

    def _backfill_business_users(self):
        """Mark existing shop owners as business role + set created_by when missing."""
        updated_users = 0
        for profile in UserProfile.objects.select_related("user", "business").filter(
            business__isnull=False
        ):
            user = profile.user
            if user.platform_role in ("", None) or user.platform_role == "business":
                if user.platform_role != "business" and not (
                    user.is_staff or user.is_superuser or user.platform_role == "super_admin"
                ):
                    user.platform_role = "business"
                    user.save(update_fields=["platform_role"])
                    updated_users += 1
                elif user.platform_role != "super_admin" and not user.is_superuser:
                    if user.platform_role != "business":
                        # Keep partners/clients if they somehow have a profile
                        pass
                    elif user.email.startswith("seed") or user.email.startswith("demo."):
                        user.platform_role = "business"
                        user.save(update_fields=["platform_role"])

            business = profile.business
            if business and not business.created_by_id:
                business.created_by = user
                business.save(update_fields=["created_by"])

        # Explicitly set demo + seed admins
        for email in User.objects.filter(
            email__in=["demo.admin@test.com", "demo.staff@test.com"]
        ).exclude(platform_role="super_admin"):
            if email.email == "demo.staff@test.com":
                email.platform_role = "business"
            else:
                email.platform_role = "business"
            email.save(update_fields=["platform_role"])

        User.objects.filter(email__startswith="seed").exclude(
            platform_role="super_admin"
        ).update(platform_role="business")

        self.stdout.write(f"Backfilled business owners / created_by (touched≈{updated_users}).")

    def _ensure_partner_listings(self, partners):
        specs = [
            (
                partners[0],
                "Partner Glow Studio",
                "salon",
                "9898980101",
                "Vesu Circle, Surat",
            ),
            (
                partners[0],
                "Partner Care Dental",
                "dentist",
                "9898980102",
                "Adajan Patiya, Surat",
            ),
            (
                partners[1],
                "Partner Fit Hub",
                "gym",
                "9898980201",
                "Varachha Road, Surat",
            ),
        ]
        listings = []
        for partner, name, industry, phone, address in specs:
            business = Business.objects.filter(name=name).first()
            if not business:
                business = create_partner_listing(
                    partner,
                    name=name,
                    industry_type=industry,
                    public_phone=phone,
                )
                business.public_address = address
                business.public_email = f"hello@{business.slug}.test"
                business.hero_title = name
                business.hero_subtitle = "Listed by a SuratBazar marketing partner."
                business.save()
                ensure_starter_categories(business)
                ensure_default_hours(business)
                cat = ServiceCategory.objects.filter(business=business).first()
                if cat:
                    Service.objects.update_or_create(
                        category=cat,
                        name="Consultation",
                        defaults={
                            "description": "Intro consult",
                            "duration_mins": 30,
                            "price": Decimal("299.00"),
                            "is_active": True,
                        },
                    )
            else:
                if business.created_by_id != partner.id:
                    business.created_by = partner
                    business.save(update_fields=["created_by"])

            business.profile_setup_completed = True
            business.listing_plan = "pro"
            if not (business.website_url or "").strip():
                business.website_url = f"https://{business.slug}.example.test"
            if not (business.public_address or "").strip():
                business.public_address = address
            business.save()
            self._ensure_sample_products(business)
            listings.append(business)
            self.stdout.write(f"Partner listing: {business.name} (/b/{business.slug}/)")
        return listings

    def _ensure_sample_products(self, business):
        specs = [
            ("Starter Kit", "Recommended starter pack for new customers.", "499.00"),
            ("Membership Card", "Priority booking + member-only offers.", "1999.00"),
            ("Care Bundle", "Popular add-on bundle sold in-store.", "799.00"),
        ]
        for name, description, price in specs:
            Product.objects.update_or_create(
                business=business,
                name=name,
                defaults={
                    "description": description,
                    "price": Decimal(price),
                    "is_active": True,
                },
            )

    def _assign_partners_to_existing(self, partners):
        # Assign partner02/03 onto a few directory / demo businesses if present
        names = [
            "Aura Glow Salon",
            "SmileCare Dental Clinic",
            "Demo Glow Studio",
            "PawPalace Pet Clinic",
        ]
        businesses = list(Business.objects.filter(name__in=names))
        if not businesses:
            businesses = list(Business.objects.exclude(created_by__in=partners)[:4])

        for i, business in enumerate(businesses):
            partner = partners[(i % (len(partners) - 1)) + 1]  # prefer 02/03
            assign_partner_to_business(partner, business)
            self.stdout.write(f"Assigned {partner.email} → {business.name}")

    def _ensure_enquiries(self, clients, partners, listings):
        # One enquiry from each client to a mix of partner + demo + directory businesses
        targets = list(listings)
        demo = Business.objects.filter(name="Demo Glow Studio").first()
        if demo:
            targets.insert(0, demo)
        extra = Business.objects.filter(profile_setup_completed=True).exclude(
            id__in=[b.id for b in targets]
        )[:3]
        targets.extend(extra)
        if not targets:
            return 0

        count = 0
        messages = [
            ("Availability?", "Do you have appointments this weekend?"),
            ("Pricing", "Please share your starting package price."),
            ("Product enquiry", "Do you still stock your Membership Card / starter kit?"),
        ]
        for i, client in enumerate(clients):
            business = targets[i % len(targets)]
            subject, body = messages[i % len(messages)]
            enquiry, created = Enquiry.objects.get_or_create(
                business=business,
                client=client,
                subject=subject,
                defaults={"status": "open"},
            )
            if created or not enquiry.messages.exists():
                EnquiryMessage.objects.get_or_create(
                    enquiry=enquiry,
                    sender=client,
                    body=body,
                )
                # Partner / owner reply on first enquiry
                if i == 0 and business.created_by_id:
                    reply_user = business.created_by
                    EnquiryMessage.objects.get_or_create(
                        enquiry=enquiry,
                        sender=reply_user,
                        body="Thanks for writing in — yes, Saturdays 11am–2pm are open.",
                    )
                    enquiry.status = "replied"
                    enquiry.save(update_fields=["status"])
            count += 1
            self.stdout.write(
                f"Enquiry: {client.email} → {business.name} [{enquiry.status}]"
            )
        return count
