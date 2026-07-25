from django.test import TestCase
from django.urls import reverse
from users.models import User, Business, UserProfile


class AuthViewTests(TestCase):
    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to your dashboard")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_login_rejects_external_next_redirect(self):
        user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="test1234",
        )
        response = self.client.post(
            f"{reverse('login')}?next=https://evil.example/path",
            data={"email": user.email, "password": "test1234"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/dashboard/")

    def test_business_profile_page_updates_landing_content(self):
        business = Business.objects.create(name="Glow Spa", industry_type="salon", timezone="Asia/Kolkata")
        user = User.objects.create_user(username="owner@test.com", email="owner@test.com", password="test1234")
        UserProfile.objects.create(user=user, business=business, role="admin")
        self.client.login(username="owner@test.com", password="test1234")

        response = self.client.post(
            reverse("business_profile"),
            data={
                "name": "Glow Spa",
                "industry_type": "salon",
                "hero_title": "Luxury Care at Glow Spa",
                "hero_subtitle": "Premium services with expert staff.",
                "hero_image_url": "https://example.com/hero.jpg",
                "public_phone": "9999999999",
                "public_email": "hello@glowspa.com",
                "public_address": "Main Road, Bengaluru",
                "website_url": "",
                "map_embed_url": "https://maps.google.com/example",
                "testimonial_quote": "Amazing service!",
                "testimonial_author": "Priya S.",
            },
        )
        self.assertEqual(response.status_code, 200)
        business.refresh_from_db()
        self.assertEqual(business.hero_title, "Luxury Care at Glow Spa")
        self.assertEqual(business.hero_image_url, "https://example.com/hero.jpg")
        self.assertEqual(business.public_hero_image_url, "https://example.com/hero.jpg")
        self.assertEqual(business.public_email, "hello@glowspa.com")
        self.assertTrue(business.profile_setup_completed)

    def test_free_plan_custom_hero_shows_on_home_directory(self):
        from core.services import bust_directory_cache
        from catalog.models import ServiceCategory, Service

        business = Business.objects.create(
            name="Photo Shop Free",
            industry_type="salon",
            timezone="Asia/Kolkata",
            public_phone="9111111111",
            public_address="Vesu, Surat",
            hero_image_url="https://cdn.example.com/my-shop.jpg",
            listing_plan="free",
            profile_setup_completed=True,
        )
        category = ServiceCategory.objects.create(business=business, name="Hair")
        Service.objects.create(
            category=category,
            name="Cut",
            duration_mins=30,
            price="199.00",
            is_active=True,
        )
        bust_directory_cache()
        self.assertEqual(business.public_hero_image_url, "https://cdn.example.com/my-shop.jpg")
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cdn.example.com/my-shop.jpg")
        self.assertContains(response, "Photo Shop Free")

    def test_listing_plan_can_be_updated(self):
        business = Business.objects.create(
            name="Glow Spa",
            industry_type="salon",
            timezone="Asia/Kolkata",
            listing_plan="free",
        )
        user = User.objects.create_user(
            username="plans@test.com",
            email="plans@test.com",
            password="test1234",
        )
        UserProfile.objects.create(user=user, business=business, role="admin")
        self.client.login(username="plans@test.com", password="test1234")

        response = self.client.post(
            reverse("listing_plans"),
            data={"listing_plan": "premium"},
        )
        self.assertEqual(response.status_code, 200)
        business.refresh_from_db()
        self.assertEqual(business.listing_plan, "premium")

    def test_register_collects_phone_and_redirects_to_onboarding(self):
        response = self.client.post(
            reverse("register_business"),
            data={
                "business_name": "New Glow",
                "industry_type": "restaurant",
                "public_phone": "9876543210",
                "email": "newglow@test.com",
                "password": "test12345",
                "password_confirm": "test12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/business-profile/?onboarding=1", response["Location"])
        business = Business.objects.get(name="New Glow")
        self.assertEqual(business.public_phone, "9876543210")
        self.assertEqual(business.industry_type, "restaurant")
        self.assertEqual(business.timezone, "Asia/Kolkata")
        self.assertTrue(business.hours.exists())

    def test_register_accepts_expanded_industry_categories(self):
        from users.industries import industry_choices_flat

        self.assertGreater(len(industry_choices_flat()), 5)
        response = self.client.post(
            reverse("register_business"),
            data={
                "business_name": "Fit Zone",
                "industry_type": "gym",
                "public_phone": "9876543211",
                "email": "fitzone@test.com",
                "password": "test12345",
                "password_confirm": "test12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        business = Business.objects.get(name="Fit Zone")
        self.assertEqual(business.industry_type, "gym")
