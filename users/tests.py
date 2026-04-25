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
                "hero_title": "Luxury Care at Glow Spa",
                "hero_subtitle": "Premium services with expert staff.",
                "hero_image_url": "https://example.com/hero.jpg",
                "public_phone": "9999999999",
                "public_email": "hello@glowspa.com",
                "public_address": "Main Road, Bengaluru",
                "map_embed_url": "https://maps.google.com/example",
                "testimonial_quote": "Amazing service!",
                "testimonial_author": "Priya S.",
            },
        )
        self.assertEqual(response.status_code, 200)
        business.refresh_from_db()
        self.assertEqual(business.hero_title, "Luxury Care at Glow Spa")
        self.assertEqual(business.public_email, "hello@glowspa.com")
