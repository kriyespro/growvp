from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic import View


def staff_or_superuser(user):
    return bool(
        user.is_authenticated
        and user.is_active
        and (
            user.is_staff
            or user.is_superuser
            or getattr(user, "platform_role", None) == "super_admin"
        )
    )


control_login_required = user_passes_test(
    staff_or_superuser,
    login_url="/auth/login/",
)


class ControlAccessMixin:
    """CBV mixin — staff/superuser only."""

    @method_decorator(control_login_required)
    def dispatch(self, request, *args, **kwargs):
        if not staff_or_superuser(request.user):
            raise PermissionDenied("Mission Control is staff-only.")
        return super().dispatch(request, *args, **kwargs)


class ControlStaffRequiredMixin(ControlAccessMixin, View):
    pass


# Re-export decorator for FBVs
__all__ = [
    "staff_or_superuser",
    "control_login_required",
    "ControlAccessMixin",
]
