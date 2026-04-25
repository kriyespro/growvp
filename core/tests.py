from django.test import TestCase
from django.urls import reverse
from users.models import Business
from catalog.models import ServiceCategory, Service


class PublicBusinessLandingTests(TestCase):
    def test_business_landing_uses_unique_slug_url(self):
        business = Business.objects.create(
            name="Glow Salon",
            industry_type="salon",
            timezone="Asia/Kolkata",
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
        )
        response = self.client.get(reverse("business_landing", kwargs={"business_slug": business.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The team is very professional.")
        self.assertContains(response, "care@aura.com")
        self.assertContains(response, "https://maps.google.com/aura")
