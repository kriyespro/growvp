from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from billing.models import Invoice
from booking.models import Appointment
from catalog.models import BusinessHours, Service, ServiceCategory
from crm.models import Customer
from users.models import Business, User, UserProfile


class Command(BaseCommand):
    help = "Seed demo business and realistic test data."

    def handle(self, *args, **options):
        business = self._create_business()
        admin_profile, provider_profile = self._create_users(business)
        categories = self._create_categories(business)
        services = self._create_services(categories)
        customers = self._create_customers(business)
        self._create_business_hours(business)
        appointments = self._create_appointments(
            business=business,
            services=services,
            customers=customers,
            provider=provider_profile,
        )
        self._create_invoices(business=business, appointments=appointments)

        self.stdout.write(self.style.SUCCESS("Demo seed completed successfully."))
        self.stdout.write(
            f"Business: {business.name} (/b/{business.slug}/)"
        )
        self.stdout.write("Admin login: demo.admin@test.com / test1234")
        self.stdout.write("Staff login: demo.staff@test.com / test1234")
        self.stdout.write(
            f"Profiles: admin={admin_profile.user.email}, provider={provider_profile.user.email}"
        )

    def _create_business(self):
        business, _ = Business.objects.update_or_create(
            name="Demo Glow Studio",
            defaults={
                "industry_type": "salon",
                "timezone": "Asia/Kolkata",
                "upi_id": "demoglow@upi",
                "hero_title": "Professional beauty and wellness appointments",
                "hero_subtitle": "Book trusted services in minutes and get timely reminders.",
                "public_phone": "+91 98765 43210",
                "public_email": "hello@demoglowstudio.com",
                "public_address": "21 Business Avenue, Ahmedabad",
                "testimonial_quote": "Smooth booking and zero scheduling confusion.",
                "testimonial_author": "Ritika Sharma",
            },
        )
        return business

    def _create_users(self, business):
        admin_user, _ = User.objects.update_or_create(
            email="demo.admin@test.com",
            defaults={
                "username": "demo.admin@test.com",
                "first_name": "Demo",
                "last_name": "Admin",
                "is_active": True,
            },
        )
        admin_user.set_password("test1234")
        admin_user.save(update_fields=["password"])

        provider_user, _ = User.objects.update_or_create(
            email="demo.staff@test.com",
            defaults={
                "username": "demo.staff@test.com",
                "first_name": "Demo",
                "last_name": "Stylist",
                "is_active": True,
            },
        )
        provider_user.set_password("test1234")
        provider_user.save(update_fields=["password"])

        admin_profile, _ = UserProfile.objects.update_or_create(
            user=admin_user,
            defaults={
                "business": business,
                "role": "admin",
                "phone": "+91 90000 10000",
            },
        )
        provider_profile, _ = UserProfile.objects.update_or_create(
            user=provider_user,
            defaults={
                "business": business,
                "role": "provider",
                "phone": "+91 90000 20000",
            },
        )
        return admin_profile, provider_profile

    def _create_categories(self, business):
        category_names = ["Hair", "Skin", "Nails"]
        categories = {}
        for name in category_names:
            category, _ = ServiceCategory.objects.update_or_create(
                business=business,
                name=name,
            )
            categories[name] = category
        return categories

    def _create_services(self, categories):
        service_specs = [
            ("Haircut + Styling", "Hair", 45, Decimal("499.00")),
            ("Hair Spa", "Hair", 60, Decimal("799.00")),
            ("Bridal Makeup", "Skin", 120, Decimal("3999.00")),
            ("Detan Facial", "Skin", 50, Decimal("1299.00")),
            ("Gel Manicure", "Nails", 40, Decimal("699.00")),
        ]

        services = []
        for name, category_name, duration, price in service_specs:
            service, _ = Service.objects.update_or_create(
                category=categories[category_name],
                name=name,
                defaults={
                    "description": f"{name} service for premium customer experience.",
                    "duration_mins": duration,
                    "price": price,
                    "is_active": True,
                    "image_url": "",
                },
            )
            services.append(service)
        return services

    def _create_customers(self, business):
        customer_specs = [
            ("Neha", "Patel", "+91 80000 00001", "neha@example.com"),
            ("Raj", "Shah", "+91 80000 00002", "raj@example.com"),
            ("Aarav", "Mehta", "+91 80000 00003", "aarav@example.com"),
            ("Priya", "Joshi", "+91 80000 00004", "priya@example.com"),
            ("Kiran", "Desai", "+91 80000 00005", "kiran@example.com"),
            ("Sneha", "Trivedi", "+91 80000 00006", "sneha@example.com"),
        ]
        customers = []
        for first_name, last_name, phone, email in customer_specs:
            customer, _ = Customer.objects.update_or_create(
                business=business,
                phone=phone,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "notes": "Demo customer generated for end-to-end testing.",
                },
            )
            customers.append(customer)
        return customers

    def _create_business_hours(self, business):
        for day in range(7):
            is_closed = day == 1
            BusinessHours.objects.update_or_create(
                business=business,
                day_of_week=day,
                defaults={
                    "is_closed": is_closed,
                    "start_time": None if is_closed else time(10, 0),
                    "end_time": None if is_closed else time(20, 0),
                },
            )

    def _create_appointments(self, business, services, customers, provider):
        today = timezone.localdate()
        schedule = [
            (today - timedelta(days=2), 10, 0, "completed", 0, 0),
            (today - timedelta(days=1), 12, 0, "completed", 1, 1),
            (today, 11, 0, "confirmed", 2, 2),
            (today, 14, 30, "pending", 3, 3),
            (today + timedelta(days=1), 15, 0, "confirmed", 4, 4),
            (today + timedelta(days=2), 17, 0, "no-show", 0, 5),
        ]

        appointments = []
        for appt_date, hour, minute, status, service_idx, customer_idx in schedule:
            service = services[service_idx % len(services)]
            customer = customers[customer_idx % len(customers)]
            start_time = time(hour, minute)

            start_dt = timezone.make_aware(datetime.combine(appt_date, start_time))
            end_dt = start_dt + timedelta(minutes=service.duration_mins)

            appt, _ = Appointment.objects.update_or_create(
                business=business,
                customer=customer,
                service=service,
                date=appt_date,
                start_time=start_time,
                defaults={
                    "end_time": end_dt.time(),
                    "status": status,
                    "provider": provider,
                },
            )
            appointments.append(appt)
        return appointments

    def _create_invoices(self, business, appointments):
        for appt in appointments:
            subtotal = appt.service.price
            tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
            total = (subtotal + tax).quantize(Decimal("0.01"))
            status = "paid" if appt.status == "completed" else "unpaid"
            Invoice.objects.update_or_create(
                business=business,
                appointment=appt,
                defaults={
                    "subtotal": subtotal,
                    "tax_amount": tax,
                    "total_amount": total,
                    "status": status,
                },
            )
