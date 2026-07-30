from django.db.models import Count, Q
from django.utils import timezone

from leads.models import Enquiry, EnquiryMessage
from users.models import User
from users.services import businesses_for_user, user_can_manage_business


ENQUIRY_INBOX_LIMIT = 100
VALID_ENQUIRY_STATUSES = frozenset({"open", "replied", "closed"})

QUICK_REPLY_PRESETS = (
    (
        "Thanks",
        "Thanks for reaching out! We'll get back to you shortly with details.",
    ),
    (
        "Call me",
        "Thanks for your interest. Please share a good time to call, or reply with your WhatsApp number.",
    ),
    (
        "Visit / hours",
        "You're welcome to visit us. Share your preferred date and time and we'll confirm availability.",
    ),
    (
        "Price / package",
        "Happy to help with pricing. Could you tell us which service or package you're interested in?",
    ),
    (
        "Closed loop",
        "Glad we could help. Feel free to reply here anytime if you have more questions.",
    ),
)


def enquiries_queryset_for_user(user):
    if not user or not user.is_authenticated:
        return Enquiry.objects.none()
    if user.platform_role == "client":
        qs = Enquiry.objects.filter(client=user)
    elif user.is_platform_super_admin or user.is_staff:
        qs = Enquiry.objects.all()
    else:
        business_ids = businesses_for_user(user).values_list("id", flat=True)
        qs = Enquiry.objects.filter(business_id__in=business_ids)
    return qs.select_related("business", "client").annotate(
        message_count=Count("messages", distinct=True)
    )


def enquiries_for_user(
    user,
    *,
    status="",
    business_id=None,
    q="",
    sort="-updated_at",
    limit=ENQUIRY_INBOX_LIMIT,
):
    qs = enquiries_queryset_for_user(user)
    status = (status or "").strip().lower()
    if status in VALID_ENQUIRY_STATUSES:
        qs = qs.filter(status=status)
    if business_id:
        try:
            qs = qs.filter(business_id=int(business_id))
        except (TypeError, ValueError):
            pass
    q = (q or "").strip()
    if q:
        qs = qs.filter(
            Q(subject__icontains=q)
            | Q(client__email__icontains=q)
            | Q(client__first_name__icontains=q)
            | Q(client__last_name__icontains=q)
            | Q(business__name__icontains=q)
        ).distinct()
    allowed_sorts = {
        "-updated_at": "-updated_at",
        "updated_at": "updated_at",
        "-created_at": "-created_at",
        "created_at": "created_at",
        "status": "status",
    }
    qs = qs.order_by(allowed_sorts.get(sort, "-updated_at"))
    return qs[:limit]


def user_can_access_enquiry(user, enquiry):
    if not user or not user.is_authenticated:
        return False
    if enquiry.client_id == user.id:
        return True
    return user_can_manage_business(user, enquiry.business)


def create_enquiry(*, client, business, subject, body):
    if client.platform_role != "client":
        raise ValueError("Only clients can create enquiries.")
    subject = (subject or "").strip() or f"Enquiry about {business.name}"
    body = (body or "").strip()
    if not body:
        raise ValueError("Message is required.")
    enquiry = Enquiry.objects.create(
        business=business,
        client=client,
        subject=subject,
        status="open",
    )
    EnquiryMessage.objects.create(enquiry=enquiry, sender=client, body=body)
    return enquiry


def reply_to_enquiry(*, user, enquiry, body):
    if not user_can_access_enquiry(user, enquiry):
        raise PermissionError("Cannot reply to this enquiry.")
    body = (body or "").strip()
    if not body:
        raise ValueError("Message is required.")
    msg = EnquiryMessage.objects.create(enquiry=enquiry, sender=user, body=body)
    if user.id == enquiry.client_id:
        if enquiry.status == "closed":
            enquiry.status = "open"
    else:
        enquiry.status = "replied"
    enquiry.updated_at = timezone.now()
    enquiry.save(update_fields=["status", "updated_at"])
    return msg


def set_enquiry_status(*, user, enquiry, status):
    """Partner/business/staff (or client open/close) can update status."""
    status = (status or "").strip().lower()
    if status not in VALID_ENQUIRY_STATUSES:
        raise ValueError("Invalid status.")
    if not user_can_access_enquiry(user, enquiry):
        raise PermissionError("Cannot update this enquiry.")
    if enquiry.client_id == user.id and user.platform_role == "client":
        if status not in ("open", "closed"):
            raise PermissionError("Clients can only open or close their enquiry.")
    enquiry.status = status
    enquiry.updated_at = timezone.now()
    enquiry.save(update_fields=["status", "updated_at"])
    return enquiry


def bulk_set_enquiry_status(*, user, ids, status):
    status = (status or "").strip().lower()
    if status not in VALID_ENQUIRY_STATUSES:
        raise ValueError("Invalid status.")
    ids = [int(i) for i in ids if str(i).isdigit()]
    if not ids:
        return 0
    updated = 0
    for enquiry in enquiries_queryset_for_user(user).filter(pk__in=ids):
        try:
            set_enquiry_status(user=user, enquiry=enquiry, status=status)
            updated += 1
        except PermissionError:
            continue
    return updated


def partner_enquiry_stats(partner):
    from users.services import businesses_for_partner

    biz_ids = list(businesses_for_partner(partner).values_list("id", flat=True))
    qs = Enquiry.objects.filter(business_id__in=biz_ids)
    today_start = timezone.localtime(timezone.now()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return {
        "total": qs.count(),
        "open": qs.filter(status="open").count(),
        "replied": qs.filter(status="replied").count(),
        "closed": qs.filter(status="closed").count(),
        "today": qs.filter(created_at__gte=today_start).count(),
        "needs_reply": qs.filter(status="open").count(),
    }


def partner_dashboard_stats(partner):
    from users.services import businesses_for_partner

    listings = businesses_for_partner(partner)
    listing_count = listings.count()
    plan_rows = {
        row["listing_plan"]: row["c"]
        for row in listings.values("listing_plan").annotate(c=Count("id"))
    }
    enquiry_stats = partner_enquiry_stats(partner)
    recent_enquiries = list(
        enquiries_for_user(partner, limit=8)
    )
    return {
        "listing_count": listing_count,
        "listings": listings,
        "plan_free": plan_rows.get("free", 0),
        "plan_pro": plan_rows.get("pro", 0),
        "plan_premium": plan_rows.get("premium", 0),
        "incomplete_listings": listings.filter(profile_setup_completed=False).count(),
        "created_by_me": listings.filter(created_by=partner).count(),
        "assigned_to_me": listings.filter(assigned_partners=partner)
        .exclude(created_by=partner)
        .distinct()
        .count(),
        "enquiry_stats": enquiry_stats,
        "recent_enquiries": recent_enquiries,
    }


def platform_enquiry_stats():
    return {
        "total": Enquiry.objects.count(),
        "open": Enquiry.objects.filter(status="open").count(),
        "replied": Enquiry.objects.filter(status="replied").count(),
    }


def list_marketing_partners():
    return (
        User.objects.filter(platform_role="marketing_partner")
        .annotate(
            created_business_count=Count("created_businesses", distinct=True),
            assigned_business_count=Count("assigned_businesses", distinct=True),
        )
        .prefetch_related("assigned_businesses")
        .order_by("email")
    )
