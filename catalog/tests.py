from django.test import TestCase
from catalog.forms import ServiceForm
from catalog.models import ServiceCategory
from users.models import Business


class ServiceFormTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Acme Salon",
            industry_type="salon",
            timezone="Asia/Kolkata",
        )
        self.category = ServiceCategory.objects.create(
            business=self.business,
            name="Hair",
        )

    def test_negative_price_is_rejected(self):
        form = ServiceForm(
            data={
                "category": self.category.id,
                "name": "Cut",
                "duration_mins": 30,
                "price": "-10",
                "is_active": True,
            },
            business=self.business,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_zero_duration_is_rejected(self):
        form = ServiceForm(
            data={
                "category": self.category.id,
                "name": "Cut",
                "duration_mins": 0,
                "price": "100",
                "is_active": True,
            },
            business=self.business,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("duration_mins", form.errors)
