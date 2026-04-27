from django.contrib import admin
from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied


class SuperuserAdminSite(AdminSite):
    site_header = 'Grow Vyapaar Super Admin'
    site_title = 'Grow Vyapaar Admin'
    index_title = 'Platform Control Center'

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
