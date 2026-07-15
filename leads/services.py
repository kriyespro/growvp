from django.db.models import Count, Q
from django.utils import timezone

from leads.models import Enquiry, EnquiryMessage
from users.models import User
from users.services import businesses_for_user, user_can_manage_business


def enquiries_for_user(user):
    if not user or not user.is_authenticated:
        return Enquiry.objects.none()
    if user.platform_role == "client":
        return (
            Enquiry.objects.filter(client=user)
            .select_related("business", "client")
            .annotate(message_count=Count("messages"))
        )
    if user.is_platform_super_admin or user.is_staff:
        return (
            Enquiry.objects.all()
            .select_related("business", "client")
            .annotate(message_count=Count("messages"))
        )
    business_ids = businesses_for_user(user).values_list("id", flat=True)
    return (
        Enquiry.objects.filter(business_id__in=business_ids)
        .select_related("business", "client")
        .annotate(message_count=Count("messages"))
    )


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


def partner_enquiry_stats(partner):
    from users.services import businesses_for_partner

    biz_ids = businesses_for_partner(partner).values_list("id", flat=True)
    qs = Enquiry.objects.filter(business_id__in=biz_ids)
    return {
        "total": qs.count(),
        "open": qs.filter(status="open").count(),
        "replied": qs.filter(status="replied").count(),
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
