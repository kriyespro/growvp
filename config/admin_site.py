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
