from django.test import TestCase
from catalog.forms import ServiceForm, ProductForm
from catalog.models import Product, ServiceCategory
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

    def test_free_plan_blocks_sixth_service(self):
        self.business.listing_plan = "free"
        self.business.save(update_fields=["listing_plan"])
        for i in range(5):
            from catalog.models import Service

            Service.objects.create(
                category=self.category,
                name=f"Service {i}",
                duration_mins=30,
                price="100.00",
                is_active=True,
            )
        form = ServiceForm(
            data={
                "category": self.category.id,
                "name": "Extra",
                "duration_mins": 30,
                "price": "100",
                "is_active": True,
            },
            business=self.business,
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())


class ProductFormTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Acme Salon",
            industry_type="salon",
            timezone="Asia/Kolkata",
            listing_plan="free",
        )

    def test_free_plan_blocks_products(self):
        form = ProductForm(
            data={
                "name": "Shampoo",
                "description": "",
                "price": "50.00",
                "image_url": "",
                "buy_url": "",
                "is_active": True,
            },
            business=self.business,
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())

    def test_pro_plan_allows_products(self):
        self.business.listing_plan = "pro"
        self.business.save(update_fields=["listing_plan"])
        form = ProductForm(
            data={
                "name": "Shampoo",
                "description": "",
                "price": "50.00",
                "image_url": "",
                "buy_url": "",
                "is_active": True,
            },
            business=self.business,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_pro_plan_blocks_16th_product(self):
        self.business.listing_plan = "pro"
        self.business.save(update_fields=["listing_plan"])
        for i in range(15):
            Product.objects.create(
                business=self.business,
                name=f"Product {i}",
                price="100.00",
                is_active=True,
            )
        form = ProductForm(
            data={
                "name": "Extra Product",
                "description": "",
                "price": "50.00",
                "image_url": "",
                "buy_url": "",
                "is_active": True,
            },
            business=self.business,
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
