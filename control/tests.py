from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from control.models import AdminLog
from users.models import Business, UserProfile

User = get_user_model()


class MissionControlTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(
            username="ops",
            email="ops@suratbazar.test",
            password="test1234",
            is_staff=True,
        )
        self.biz = Business.objects.create(
            name="Control Test Salon",
            industry_type="salon",
            timezone="Asia/Kolkata",
        )
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@suratbazar.test",
            password="test1234",
        )
        UserProfile.objects.create(
            user=self.owner,
            business=self.biz,
            role="admin",
            phone="9876543210",
        )

    def test_admin_requires_staff(self):
        self.client.login(username="owner", password="test1234")
        response = self.client.get(reverse("control:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_ok_for_staff(self):
        self.client.login(username="ops", password="test1234")
        response = self.client.get(reverse("control:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mission Control")
        self.assertContains(response, "Total users")

    def test_django_admin_backup_at_sd(self):
        # Unauthenticated hits Django login (backup panel still mounted at /sd/)
        response = self.client.get("/sd/")
        self.assertIn(response.status_code, (200, 302))
        # /admin/ is Mission Control, not Django admin
        self.client.login(username="ops", password="test1234")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mission Control")
        self.assertNotContains(response, "Django administration")

    def test_user_search_htmx(self):
        self.client.login(username="ops", password="test1234")
        response = self.client.get(
            reverse("control:users"),
            {"q": "owner@"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "owner@suratbazar.test")

    def test_ban_unban_logs_action(self):
        self.client.login(username="ops", password="test1234")
        response = self.client.post(reverse("control:user_ban", kwargs={"pk": self.owner.pk}))
        self.assertEqual(response.status_code, 302)
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_active)
        self.assertTrue(AdminLog.objects.filter(action="ban", target_user=self.owner).exists())

        response = self.client.post(reverse("control:user_unban", kwargs={"pk": self.owner.pk}))
        self.assertEqual(response.status_code, 302)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)

    def test_ban_rejected_on_get(self):
        self.client.login(username="ops", password="test1234")
        response = self.client.get(reverse("control:user_ban", kwargs={"pk": self.owner.pk}))
        self.assertEqual(response.status_code, 405)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)

    def test_impersonate_and_stop(self):
        self.client.login(username="ops", password="test1234")
        response = self.client.post(reverse("control:impersonate", kwargs={"pk": self.owner.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_control_impersonator_id"]), self.staff.pk)

        response = self.client.post(reverse("control:stop_impersonate"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_control_impersonator_id", self.client.session)
