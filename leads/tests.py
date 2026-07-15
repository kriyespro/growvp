from django.test import Client, TestCase
from django.urls import reverse

from leads.models import Enquiry, EnquiryMessage
from users.models import Business, User, UserProfile
from users.services import assign_partner_to_business, businesses_for_partner


class PlatformRoleTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_business_register_sets_role_and_created_by(self):
        response = self.client.post(
            reverse("register_business"),
            {
                "business_name": "Role Biz",
                "industry_type": "salon",
                "public_phone": "9876543210",
                "email": "bizrole@test.com",
                "password": "test12345",
                "password_confirm": "test12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="bizrole@test.com")
        self.assertEqual(user.platform_role, "business")
        self.assertTrue(Business.objects.filter(created_by=user, name="Role Biz").exists())

    def test_partner_register_redirects_partner_home(self):
        response = self.client.post(
            "/auth/register/?as=partner",
            {
                "email": "partner1@test.com",
                "password": "test12345",
                "password_confirm": "test12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/partner/")
        user = User.objects.get(email="partner1@test.com")
        self.assertEqual(user.platform_role, "marketing_partner")

    def test_client_register_redirects_account(self):
        response = self.client.post(
            "/auth/register/?as=client",
            {
                "email": "client1@test.com",
                "password": "test12345",
                "password_confirm": "test12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/")

    def test_role_dashboard_guards(self):
        partner = User.objects.create_user(
            username="p2@test.com",
            email="p2@test.com",
            password="test12345",
            platform_role="marketing_partner",
        )
        self.client.login(username="p2@test.com", password="test12345")
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/partner/")
        response = self.client.get("/partner/")
        self.assertEqual(response.status_code, 200)

    def test_partner_create_and_assign_listing(self):
        partner = User.objects.create_user(
            username="p3@test.com",
            email="p3@test.com",
            password="test12345",
            platform_role="marketing_partner",
        )
        other = User.objects.create_user(
            username="p4@test.com",
            email="p4@test.com",
            password="test12345",
            platform_role="marketing_partner",
        )
        self.client.login(username="p3@test.com", password="test12345")
        response = self.client.post(
            "/partner/listings/new/",
            {
                "name": "Partner Salon",
                "industry_type": "salon",
                "public_phone": "9123456789",
            },
        )
        self.assertEqual(response.status_code, 302)
        business = Business.objects.get(name="Partner Salon")
        self.assertEqual(business.created_by_id, partner.id)
        self.assertIn(business, list(businesses_for_partner(partner)))

        assign_partner_to_business(other, business)
        self.assertIn(business, list(businesses_for_partner(other)))

    def test_client_enquiry_visible_to_business_and_partner(self):
        owner = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="test12345",
            platform_role="business",
        )
        business = Business.objects.create(
            name="Enquire Me",
            industry_type="salon",
            timezone="Asia/Kolkata",
            created_by=owner,
            profile_setup_completed=True,
            public_phone="9000000000",
            public_address="Surat",
        )
        UserProfile.objects.create(user=owner, business=business, role="admin")
        partner = User.objects.create_user(
            username="p5@test.com",
            email="p5@test.com",
            password="test12345",
            platform_role="marketing_partner",
        )
        assign_partner_to_business(partner, business)
        client_user = User.objects.create_user(
            username="cli@test.com",
            email="cli@test.com",
            password="test12345",
            platform_role="client",
        )
        self.client.login(username="cli@test.com", password="test12345")
        response = self.client.post(
            f"/leads/new/{business.slug}/",
            {"subject": "Hello", "body": "Do you have slots tomorrow?"},
        )
        self.assertEqual(response.status_code, 302)
        enquiry = Enquiry.objects.get(business=business, client=client_user)
        self.assertEqual(enquiry.messages.count(), 1)

        self.client.login(username="owner@test.com", password="test12345")
        response = self.client.get("/leads/")
        self.assertContains(response, "Hello")

        self.client.login(username="p5@test.com", password="test12345")
        response = self.client.get("/leads/")
        self.assertContains(response, "Hello")

        response = self.client.post(
            f"/leads/{enquiry.pk}/",
            {"body": "Yes, 4pm is free."},
        )
        self.assertEqual(response.status_code, 302)
        enquiry.refresh_from_db()
        self.assertEqual(enquiry.status, "replied")
        self.assertEqual(EnquiryMessage.objects.filter(enquiry=enquiry).count(), 2)

    def test_login_redirects_by_role(self):
        User.objects.create_user(
            username="cli2@test.com",
            email="cli2@test.com",
            password="test12345",
            platform_role="client",
        )
        response = self.client.post(
            "/auth/login/",
            {"email": "cli2@test.com", "password": "test12345"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/")
