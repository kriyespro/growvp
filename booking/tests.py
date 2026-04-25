from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from booking.models import Appointment
from booking.forms import AppointmentForm
from catalog.models import Service, ServiceCategory
from crm.models import Customer
from users.models import Business


class PublicBookingTests(TestCase):
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
        self.service = Service.objects.create(
            category=self.category,
            name="Hair Cut",
            duration_mins=30,
            price="499.00",
            is_active=True,
        )
        self.url = reverse("public_booking", kwargs={"business_id": self.business.id})
        self.slug_url = reverse("public_booking_by_slug", kwargs={"business_slug": self.business.slug})

    def test_invalid_datetime_does_not_create_appointment(self):
        response = self.client.post(
            self.url,
            data={
                "service": self.service.id,
                "date": "not-a-date",
                "time": "10:00",
                "phone": "9999999999",
                "first_name": "Rahul",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please select a valid date and time.")
        self.assertEqual(Appointment.objects.count(), 0)

    def test_overlapping_slot_is_blocked(self):
        customer = Customer.objects.create(
            business=self.business,
            first_name="Existing",
            phone="8888888888",
        )
        Appointment.objects.create(
            business=self.business,
            customer=customer,
            service=self.service,
            date=date(2026, 4, 20),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status="confirmed",
        )

        response = self.client.post(
            self.url,
            data={
                "service": self.service.id,
                "date": "2026-04-20",
                "time": "10:15",
                "phone": "7777777777",
                "first_name": "New Customer",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This slot is already booked.")
        self.assertEqual(Appointment.objects.count(), 1)

    def test_invalid_datetime_does_not_create_customer(self):
        response = self.client.post(
            self.url,
            data={
                "service": self.service.id,
                "date": "bad-date",
                "time": "10:00",
                "phone": "9991112222",
                "first_name": "Aman",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customer.objects.count(), 0)

    def test_slug_based_public_booking_url_works(self):
        response = self.client.get(self.slug_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.business.name)


class AppointmentFormTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Acme Salon",
            industry_type="salon",
            timezone="Asia/Kolkata",
        )
        category = ServiceCategory.objects.create(business=self.business, name="Hair")
        self.service = Service.objects.create(
            category=category,
            name="Hair Cut",
            duration_mins=30,
            price="499.00",
            is_active=True,
        )
        self.customer = Customer.objects.create(
            business=self.business,
            first_name="Ravi",
            phone="1234567890",
        )

    def test_end_time_must_be_after_start_time(self):
        form = AppointmentForm(
            data={
                "customer": self.customer.id,
                "service": self.service.id,
                "date": "2026-04-20",
                "start_time": "11:00",
                "end_time": "10:30",
            },
            business=self.business,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("end_time", form.errors)

    def test_form_rejects_overlapping_appointments(self):
        Appointment.objects.create(
            business=self.business,
            customer=self.customer,
            service=self.service,
            date=date(2026, 4, 20),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status="confirmed",
        )
        form = AppointmentForm(
            data={
                "customer": self.customer.id,
                "service": self.service.id,
                "date": "2026-04-20",
                "start_time": "10:15",
                "end_time": "10:45",
            },
            business=self.business,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
