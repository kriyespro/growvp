from django.test import TestCase
from django.urls import reverse
from users.models import User, Business, UserProfile
from crm.models import Customer


class CrmViewTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Acme Salon",
            industry_type="salon",
            timezone="Asia/Kolkata",
        )
        self.user = User.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
            password="test1234",
        )
        UserProfile.objects.create(user=self.user, business=self.business, role="admin")
        self.client.login(username="admin@test.com", password="test1234")

    def test_existing_customer_phone_updates_instead_of_duplicate(self):
        Customer.objects.create(
            business=self.business,
            first_name="Old",
            phone="9999999999",
        )
        response = self.client.post(
            reverse("customers_list"),
            data={
                "first_name": "New",
                "last_name": "Name",
                "phone": "9999999999",
                "email": "new@example.com",
                "notes": "updated",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customer.objects.count(), 1)
        customer = Customer.objects.get()
        self.assertEqual(customer.first_name, "New")
