from datetime import time

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import Business, User, UserProfile
from catalog.models import BusinessHours, Product, ServiceCategory, Service
from crm.models import Customer
from booking.models import Appointment


class BusinessDirectoryTests(TestCase):
    def setUp(self):
        from core.services import bust_directory_cache

        bust_directory_cache()
        self.salon = Business.objects.create(
            name="Glow Salon",
            industry_type="salon",
            timezone="Asia/Kolkata",
            public_phone="9999999999",
            public_address="Ring Road, Surat",
            hero_title="Beauty done right",
            profile_setup_completed=True,
        )
        self.dentist = Business.objects.create(
            name="Smile Dental",
            industry_type="dentist",
            timezone="Asia/Kolkata",
            public_phone="8888888888",
            profile_setup_completed=True,
        )
        self.call_only = Business.objects.create(
            name="Phone Only Optical",
            industry_type="optical",
            timezone="Asia/Kolkata",
            public_phone="7777777777",
            public_address="Adajan, Surat",
            profile_setup_completed=False,
        )
        category = ServiceCategory.objects.create(business=self.salon, name="Hair")
        Service.objects.create(
            category=category,
            name="Haircut",
            duration_mins=30,
            price="499.00",
            is_active=True,
        )
        Service.objects.create(
            category=category,
            name="Color",
            duration_mins=60,
            price="1499.00",
            is_active=True,
        )
        today = timezone.localdate().weekday()
        BusinessHours.objects.create(
            business=self.salon,
            day_of_week=today,
            start_time=time(0, 0),
            end_time=time(23, 59),
            is_closed=False,
        )

    def test_home_page_is_business_directory(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SuratBazar")
        self.assertContains(response, "Glow Salon")
        self.assertContains(response, "Smile Dental")
        self.assertContains(response, "Haircut")
        self.assertContains(response, "₹499")
        self.assertContains(response, "₹1499")
        self.assertContains(response, "/b/glow-salon/")
        self.assertContains(response, "Open now")
        self.assertContains(response, "Book online")
        self.assertContains(response, "Verified")
        self.assertContains(response, "Open right now")

    def test_directory_search_filters_by_query_and_industry(self):
        response = self.client.get(
            reverse("directory_search"),
            {"q": "Glow", "industry": "salon"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Glow Salon")
        self.assertNotContains(response, "Smile Dental")

    def test_directory_filters_bookable_and_verified(self):
        bookable = self.client.get(reverse("directory_search"), {"bookable": "1"})
        self.assertContains(bookable, "Glow Salon")
        self.assertNotContains(bookable, "Phone Only Optical")

        verified = self.client.get(reverse("directory_search"), {"verified": "1"})
        self.assertContains(verified, "Glow Salon")
        self.assertContains(verified, "Smile Dental")
        self.assertNotContains(verified, "Phone Only Optical")

    def test_directory_filter_open_now(self):
        response = self.client.get(
            reverse("directory_search"),
            {"availability": "open"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Glow Salon")
        self.assertNotContains(response, "Smile Dental")

    def test_directory_sort_popular_by_bookings(self):
        provider_user = User.objects.create_user(
            username="provider@test.com",
            email="provider@test.com",
            password="test1234",
        )
        provider = UserProfile.objects.create(
            user=provider_user,
            business=self.salon,
            role="provider",
        )
        customer = Customer.objects.create(
            business=self.salon,
            first_name="Riya",
            phone="9000000001",
        )
        service = Service.objects.filter(category__business=self.salon).first()
        Appointment.objects.create(
            business=self.salon,
            customer=customer,
            service=service,
            provider=provider,
            date=timezone.localdate(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status="confirmed",
        )
        response = self.client.get(reverse("directory_search"), {"sort": "popular"})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertLess(content.index("Glow Salon"), content.index("Smile Dental"))
        self.assertContains(response, "1 booking")

    def test_directory_does_not_force_login_redirect(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "List your business")

    def test_directory_kpi_stats_present(self):
        response = self.client.get(reverse("landing"))
        self.assertContains(response, "listed")
        self.assertContains(response, "Open now")
        self.assertContains(response, "Book online")

    def test_directory_results_capped_at_page_limit(self):
        from core.services import bust_directory_cache
        from core.views import DIRECTORY_LIST_LIMIT

        for i in range(DIRECTORY_LIST_LIMIT + 5):
            Business.objects.create(
                name=f"Extra Shop {i}",
                industry_type="salon",
                timezone="Asia/Kolkata",
                public_phone=f"9000000{i:03d}",
                profile_setup_completed=True,
            )
        bust_directory_cache()
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Showing")
        self.assertContains(response, str(DIRECTORY_LIST_LIMIT))
        self.assertContains(response, "Showing top")


class PublicBusinessLandingTests(TestCase):
    def test_business_landing_uses_unique_slug_url(self):
        business = Business.objects.create(
            name="Glow Salon",
            industry_type="salon",
            timezone="Asia/Kolkata",
            public_phone="9999999999",
        )
        category = ServiceCategory.objects.create(business=business, name="Hair")
        Service.objects.create(
            category=category,
            name="Trim",
            duration_mins=20,
            price="199.00",
            is_active=True,
        )
        response = self.client.get(reverse("business_landing", kwargs={"business_slug": business.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Glow Salon")
        self.assertContains(response, f"/booking/{business.slug}/")

    def test_business_landing_shows_service_details_price_and_image(self):
        business = Business.objects.create(
            name="Polish Studio",
            industry_type="salon",
            timezone="Asia/Kolkata",
        )
        category = ServiceCategory.objects.create(business=business, name="Nails")
        Service.objects.create(
            category=category,
            name="Gel Polish",
            description="Premium gel finish",
            image_url="https://example.com/gel.jpg",
            duration_mins=45,
            price="899.00",
            is_active=True,
        )

        response = self.client.get(reverse("business_landing", kwargs={"business_slug": business.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gel Polish")
        self.assertContains(response, "Premium gel finish")
        self.assertContains(response, "₹899.00")
        self.assertContains(response, "https://example.com/gel.jpg")

    def test_business_landing_shows_contact_and_testimonial(self):
        business = Business.objects.create(
            name="Aura Clinic",
            industry_type="dentist",
            timezone="Asia/Kolkata",
            public_phone="8888888888",
            public_email="care@aura.com",
            public_address="MG Road, Pune",
            map_embed_url="https://maps.google.com/aura",
            testimonial_quote="The team is very professional.",
            testimonial_author="Rohit K.",
            listing_plan="pro",
        )
        response = self.client.get(reverse("business_landing", kwargs={"business_slug": business.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The team is very professional.")
        self.assertContains(response, "care@aura.com")
        self.assertContains(response, "https://maps.google.com/aura")

    def test_free_plan_hides_pro_trust_tools(self):
        business = Business.objects.create(
            name="Free Aura",
            industry_type="dentist",
            timezone="Asia/Kolkata",
            public_phone="8888888888",
            public_email="hidden@aura.com",
            public_address="MG Road, Pune",
            map_embed_url="https://maps.google.com/free-aura",
            testimonial_quote="Should stay private on Free.",
            testimonial_author="Guest",
            listing_plan="free",
        )
        response = self.client.get(reverse("business_landing", kwargs={"business_slug": business.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Should stay private on Free.")
        self.assertNotContains(response, "hidden@aura.com")
        self.assertNotContains(response, "https://maps.google.com/free-aura")
        self.assertNotContains(response, "Copy link")
        self.assertContains(response, "8888888888")

    def test_business_landing_shows_hours_and_directory_link(self):
        business = Business.objects.create(
            name="Hour Clinic",
            industry_type="dentist",
            timezone="Asia/Kolkata",
            public_phone="7777777777",
        )
        BusinessHours.objects.create(
            business=business,
            day_of_week=0,
            start_time="09:00",
            end_time="18:00",
            is_closed=False,
        )
        category = ServiceCategory.objects.create(business=business, name="Care")
        Service.objects.create(
            category=category,
            name="Checkup",
            duration_mins=20,
            price="299.00",
            is_active=True,
        )
        response = self.client.get(reverse("business_landing", kwargs={"business_slug": business.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SuratBazar directory")
        self.assertContains(response, "Hours")
        self.assertContains(response, "Monday")
        self.assertContains(response, "1 service")
        self.assertContains(response, "₹299.00")

    def test_business_landing_rich_glance_whatsapp_directions_tabs(self):
        business = Business.objects.create(
            name="Rich Clinic",
            industry_type="dentist",
            timezone="Asia/Kolkata",
            public_phone="9876543210",
            public_address="Vesu, Surat",
            profile_setup_completed=True,
        )
        hair = ServiceCategory.objects.create(business=business, name="Consult")
        treatment = ServiceCategory.objects.create(business=business, name="Treatment")
        Service.objects.create(
            category=hair,
            name="Consulta",
            duration_mins=15,
            price="199.00",
            is_active=True,
        )
        Service.objects.create(
            category=treatment,
            name="Cleaning",
            duration_mins=40,
            price="799.00",
            is_active=True,
        )
        response = self.client.get(
            reverse("business_landing", kwargs={"business_slug": business.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All services")
        self.assertContains(response, "Featured services")
        self.assertContains(response, "Verified")
        self.assertContains(response, "WhatsApp")
        self.assertContains(response, "wa.me/919876543210")
        self.assertContains(response, "Directions")
        self.assertContains(response, "google.com/maps")
        self.assertContains(response, "Consult")
        self.assertContains(response, "Treatment")
        self.assertContains(response, "₹199")
        self.assertContains(response, "₹799")
        self.assertContains(response, "At a glance")

    def test_business_landing_shows_products_and_website_for_pro(self):
        business = Business.objects.create(
            name="Pro Pet Shop",
            industry_type="pet",
            timezone="Asia/Kolkata",
            public_phone="9123456789",
            public_address="Katargam, Surat",
            website_url="https://propet.example.com",
            listing_plan="pro",
            profile_setup_completed=True,
        )
        category = ServiceCategory.objects.create(business=business, name="Grooming")
        Service.objects.create(
            category=category,
            name="Full Groom",
            duration_mins=60,
            price="899.00",
            is_active=True,
        )
        Product.objects.create(
            business=business,
            name="Organic Shampoo",
            description="Gentle coat wash",
            price="349.00",
            is_active=True,
        )
        response = self.client.get(
            reverse("business_landing", kwargs={"business_slug": business.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Products")
        self.assertContains(response, "Organic Shampoo")
        self.assertContains(response, "₹349")
        self.assertContains(response, "Enquire")
        self.assertContains(
            response, f"/leads/new/{business.slug}/?product="
        )
        self.assertContains(response, "Website")
        self.assertContains(response, "https://propet.example.com")
        self.assertContains(response, "Pro")
        self.assertContains(response, "Send enquiry")

    def test_free_plan_hides_website_button(self):
        business = Business.objects.create(
            name="Free Optical",
            industry_type="optical",
            timezone="Asia/Kolkata",
            public_phone="9000000000",
            public_address="Varachha, Surat",
            website_url="https://freebiz.example.com",
            listing_plan="free",
            profile_setup_completed=True,
        )
        response = self.client.get(
            reverse("business_landing", kwargs={"business_slug": business.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "https://freebiz.example.com")

    def test_pricing_page_compares_yearly_plans(self):
        response = self.client.get(reverse("pricing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compare plans")
        self.assertContains(response, "₹999")
        self.assertContains(response, "₹3,999")
        self.assertContains(response, "per year")
        self.assertContains(response, "Bookable services")
        self.assertContains(response, "Map embed")
        self.assertContains(response, "Remove platform branding")
        self.assertContains(response, "Featured in directory")
        self.assertContains(response, "Free")
        self.assertContains(response, "Pro")
        self.assertContains(response, "Premium")

    def test_robots_and_sitemap(self):
        business = Business.objects.create(
            name="SEO Clinic",
            industry_type="dentist",
            timezone="Asia/Kolkata",
            profile_setup_completed=True,
            public_phone="9111111111",
            public_address="Adajan, Surat",
        )
        robots = self.client.get(reverse("robots_txt"))
        self.assertEqual(robots.status_code, 200)
        self.assertContains(robots, "Sitemap:")
        self.assertContains(robots, "Allow: /surat/")
        self.assertContains(robots, "Disallow: /admin/")
        self.assertContains(robots, "Disallow: /dashboard/")

        sitemap = self.client.get(reverse("sitemap_xml"))
        self.assertEqual(sitemap.status_code, 200)
        self.assertContains(sitemap, "/pricing/")
        self.assertContains(sitemap, "/surat/")
        self.assertContains(sitemap, "/surat/dentist/")
        self.assertContains(sitemap, "/surat/dentist/adajan/")
        self.assertContains(sitemap, f"/b/{business.slug}/")
        self.assertContains(sitemap, f"/booking/{business.slug}/")

    def test_programmatic_surat_pages(self):
        Business.objects.create(
            name="Adajan Smiles",
            industry_type="dentist",
            timezone="Asia/Kolkata",
            profile_setup_completed=True,
            public_phone="9222222222",
            public_address="Adajan, Surat",
        )
        hub = self.client.get(reverse("surat_hub"))
        self.assertEqual(hub.status_code, 200)
        self.assertContains(hub, "Local businesses in Surat")
        self.assertContains(hub, "/surat/dentist/")
        self.assertContains(hub, "application/ld+json")
        self.assertContains(hub, "BreadcrumbList")

        industry = self.client.get(
            reverse("surat_industry", kwargs={"industry": "dentist"})
        )
        self.assertEqual(industry.status_code, 200)
        self.assertContains(industry, "Adajan Smiles")
        self.assertContains(industry, "/surat/dentist/adajan/")
        self.assertContains(industry, "ItemList")

        area = self.client.get(
            reverse(
                "surat_industry_area",
                kwargs={"industry": "dentist", "area_slug": "adajan"},
            )
        )
        self.assertEqual(area.status_code, 200)
        self.assertContains(area, "Adajan")
        self.assertContains(area, "Adajan Smiles")

        missing = self.client.get(
            reverse(
                "surat_industry_area",
                kwargs={"industry": "dentist", "area_slug": "no-such-area"},
            )
        )
        self.assertEqual(missing.status_code, 404)

    def test_business_landing_seo_meta_and_jsonld(self):
        business = Business.objects.create(
            name="SEO Glow",
            industry_type="salon",
            timezone="Asia/Kolkata",
            hero_subtitle="Premium cuts near Vesu with online booking.",
            public_address="Vesu, Surat",
            profile_setup_completed=True,
        )
        response = self.client.get(
            reverse("business_landing", kwargs={"business_slug": business.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="description"')
        self.assertContains(response, "Premium cuts near Vesu")
        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, "application/ld+json")
        self.assertContains(response, "LocalBusiness")
        self.assertContains(response, "BreadcrumbList")
        self.assertContains(response, "SEO Glow")
        self.assertContains(response, "/surat/salon/")
        self.assertContains(response, "/surat/salon/vesu/")

