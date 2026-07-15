from django.contrib import admin
from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce


class SuperuserAdminSite(AdminSite):
    site_header = 'SuratBazar Django Admin'
    site_title = 'SuratBazar /sd'
    index_title = 'Backup admin panel'
    index_template = 'admin/custom_index.html'

    def has_permission(self, request):
        user = request.user
        return user.is_active and user.is_authenticated and user.is_superuser

    def admin_view(self, view, cacheable=False):
        wrapped_view = super().admin_view(view, cacheable=cacheable)

        def superuser_only(request, *args, **kwargs):
            if request.user.is_authenticated and not request.user.is_superuser:
                raise PermissionDenied('Only superusers can access this admin.')
            return wrapped_view(request, *args, **kwargs)

        return superuser_only

    def each_context(self, request):
        context = super().each_context(request)
        from users.models import User, Business
        from booking.models import Appointment
        from billing.models import Invoice

        total_users = User.objects.count()
        total_businesses = Business.objects.count()
        total_bookings = Appointment.objects.count()
        total_revenue = Invoice.objects.filter(status='paid').aggregate(
            total=Coalesce(
                Sum('total_amount'),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            )
        )['total']
        paid_businesses = Invoice.objects.filter(status='paid').aggregate(
            count=Count('business', distinct=True)
        )['count'] or 0
        trial_businesses = max(total_businesses - paid_businesses, 0)

        context['dashboard_kpis'] = {
            'total_users': total_users,
            'total_businesses': total_businesses,
            'paid_businesses': paid_businesses,
            'trial_businesses': trial_businesses,
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
        }
        return context


class DefaultStaffAdminSite(AdminSite):
    site_header = 'Django administration'
    site_title = 'Django site admin'
    index_title = 'Site administration'


default_admin_site = DefaultStaffAdminSite(name='default_admin')


def get_default_admin_site():
    if default_admin_site._registry:
        return default_admin_site

    for model, model_admin in admin.site._registry.items():
        default_admin_site.register(model, model_admin.__class__)
    return default_admin_site
