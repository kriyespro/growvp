from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from users.services import home_url_for_user


def require_platform_role(*roles):
    """Require authenticated user with one of the given platform_role values."""

    def decorator(view_func):
        @login_required(login_url="/auth/login/")
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            allowed = set(roles)
            if "super_admin" in allowed and (
                user.is_staff or user.is_superuser or user.platform_role == "super_admin"
            ):
                return view_func(request, *args, **kwargs)
            if user.platform_role in allowed:
                return view_func(request, *args, **kwargs)
            return redirect(home_url_for_user(user))

        return _wrapped

    return decorator


def require_business_dashboard(view_func):
    """Business staff dashboard — needs platform_role=business + profile + business."""

    @login_required(login_url="/auth/login/")
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if user.platform_role != "business" and not (
            user.is_staff and getattr(user, "profile", None)
        ):
            if user.platform_role in (
                "super_admin",
                "marketing_partner",
                "client",
            ) or user.is_staff:
                return redirect(home_url_for_user(user))
        profile = getattr(user, "profile", None)
        if not profile or not profile.business_id:
            return redirect(home_url_for_user(user))
        return view_func(request, *args, **kwargs)

    return _wrapped


def assert_can_manage_business(user, business):
    from users.services import user_can_manage_business

    if not user_can_manage_business(user, business):
        raise PermissionDenied("You cannot manage this listing.")
