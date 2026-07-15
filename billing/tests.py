from django.test import TestCase
from django.urls import reverse
from decimal import Decimal

from users.models import User, Business, UserProfile
from catalog.models import ServiceCategory, Service
from crm.models import Customer
from booking.models import Appointment
from billing.models import Invoice


class BillingCheckoutTests(TestCase):
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
        category = ServiceCategory.objects.create(business=self.business, name="Hair")
        self.service = Service.objects.create(
            category=category,
            name="Hair Cut",
            duration_mins=30,
            price="500.00",
            is_active=True,
        )
        customer = Customer.objects.create(business=self.business, first_name="Aman", phone="1234567890")
        self.appointment = Appointment.objects.create(
            business=self.business,
            customer=customer,
            service=self.service,
            date="2026-04-20",
            start_time="10:00",
            end_time="10:30",
            status="confirmed",
        )
        self.client.login(username="admin@test.com", password="test1234")

    def test_checkout_updates_existing_invoice_totals(self):
        invoice = Invoice.objects.create(
            business=self.business,
            appointment=self.appointment,
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            total_amount=Decimal("118.00"),
            status="unpaid",
        )
        response = self.client.get(reverse("checkout_modal", kwargs={"appointment_id": self.appointment.id}))
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, Decimal("500.00"))
        self.assertEqual(invoice.tax_amount, Decimal("90.00"))
        self.assertEqual(invoice.total_amount, Decimal("590.00"))

    def test_checkout_marks_paid_only_with_flag(self):
        response = self.client.post(reverse("checkout_modal", kwargs={"appointment_id": self.appointment.id}), data={})
        self.assertEqual(response.status_code, 200)
        invoice = Invoice.objects.get(appointment=self.appointment)
        self.assertEqual(invoice.status, "unpaid")
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "confirmed")

    def test_paid_invoice_totals_are_not_rewritten_by_later_price_changes(self):
        invoice = Invoice.objects.create(
            business=self.business,
            appointment=self.appointment,
            subtotal=Decimal("500.00"),
            tax_amount=Decimal("90.00"),
            total_amount=Decimal("590.00"),
            status="paid",
        )
        self.service.price = Decimal("900.00")
        self.service.save(update_fields=["price"])

        response = self.client.get(reverse("checkout_modal", kwargs={"appointment_id": self.appointment.id}))
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, Decimal("500.00"))
        self.assertEqual(invoice.tax_amount, Decimal("90.00"))
        self.assertEqual(invoice.total_amount, Decimal("590.00"))

