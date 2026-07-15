from django.db.models import Q

from users.models import Business, User


PLATFORM_HOME = {
    "super_admin": "/admin/",
    "marketing_partner": "/partner/",
    "business": "/dashboard/",
    "client": "/account/",
}


def home_url_for_user(user):
    if not user or not user.is_authenticated:
        return "/auth/login/"
    if user.is_staff or user.is_superuser or user.platform_role == "super_admin":
        return PLATFORM_HOME["super_admin"]
    return PLATFORM_HOME.get(user.platform_role, "/dashboard/")


def businesses_for_partner(user):
    """Listings a marketing partner created or is assigned to."""
    if not user or not user.is_authenticated:
        return Business.objects.none()
    return (
        Business.objects.filter(Q(created_by=user) | Q(assigned_partners=user))
        .distinct()
        .order_by("-created_at")
    )


def businesses_for_user(user):
    """Businesses the user can manage (owner staff or partner)."""
    if not user or not user.is_authenticated:
        return Business.objects.none()
    if user.is_platform_super_admin or user.is_staff:
        return Business.objects.all().order_by("-created_at")
    if user.platform_role == "marketing_partner":
        return businesses_for_partner(user)
    profile = getattr(user, "profile", None)
    if profile and profile.business_id:
        return Business.objects.filter(pk=profile.business_id)
    return Business.objects.none()


def user_can_manage_business(user, business):
    if not user or not user.is_authenticated or business is None:
        return False
    if user.is_platform_super_admin or user.is_staff:
        return True
    if user.platform_role == "marketing_partner":
        if business.created_by_id == user.id:
            return True
        return business.assigned_partners.filter(pk=user.pk).exists()
    profile = getattr(user, "profile", None)
    return bool(profile and profile.business_id == business.id)


def assign_partner_to_business(partner, business):
    if partner.platform_role != "marketing_partner":
        raise ValueError("User is not a marketing partner.")
    business.assigned_partners.add(partner)


def unassign_partner_from_business(partner, business):
    business.assigned_partners.remove(partner)


def create_partner_listing(partner, *, name, industry_type, public_phone=""):
    if partner.platform_role != "marketing_partner":
        raise ValueError("Only marketing partners can create partner listings.")
    business = Business.objects.create(
        name=name,
        industry_type=industry_type,
        public_phone=public_phone,
        timezone="Asia/Kolkata",
        created_by=partner,
    )
    return business
