from django.contrib.sessions.models import Session
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from control.models import AdminLog
from users.models import Business, User


IMPERSONATOR_SESSION_KEY = "_control_impersonator_id"


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_admin_action(actor, action, message, target_user=None, request=None):
    return AdminLog.objects.create(
        actor=actor,
        action=action,
        target_user=target_user,
        message=message,
        ip_address=client_ip(request) if request is not None else None,
    )


def get_dashboard_stats():
    """Live KPIs for Mission Control dashboard cards."""
    from billing.models import Invoice
    from booking.models import Appointment

    now = timezone.now()
    today_start = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = User.objects.count()
    total_businesses = Business.objects.count()
    signups_today = User.objects.filter(date_joined__gte=today_start).count()
    active_sessions = Session.objects.filter(expire_date__gte=now).count()

    paid_agg = Invoice.objects.filter(status="paid").aggregate(
        revenue=Coalesce(
            Sum("total_amount"),
            Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
        ),
        paid_businesses=Count("business", distinct=True),
    )
    total_revenue = paid_agg["revenue"] or 0
    paid_businesses = paid_agg["paid_businesses"] or 0
    trial_businesses = max(total_businesses - paid_businesses, 0)

    bookings_total = Appointment.objects.count()
    bookings_today = Appointment.objects.filter(created_at__gte=today_start).count()

    plan_counts = {
        row["listing_plan"]: row["c"]
        for row in Business.objects.values("listing_plan").annotate(c=Count("id"))
    }

    role_counts = {
        row["platform_role"]: row["c"]
        for row in User.objects.values("platform_role").annotate(c=Count("id"))
    }
    partners = role_counts.get("marketing_partner", 0)
    clients = role_counts.get("client", 0)
    partner_created = Business.objects.filter(created_by__platform_role="marketing_partner").count()
    partner_assigned = (
        Business.objects.filter(assigned_partners__isnull=False).distinct().count()
    )

    from leads.services import platform_enquiry_stats

    enquiry_stats = platform_enquiry_stats()

    industry_top = list(
        Business.objects.values("industry_type")
        .annotate(c=Count("id"))
        .order_by("-c")[:5]
    )

    return {
        "total_users": total_users,
        "total_businesses": total_businesses,
        "signups_today": signups_today,
        "active_sessions": active_sessions,
        "total_revenue": total_revenue,
        "paid_businesses": paid_businesses,
        "trial_businesses": trial_businesses,
        "bookings_total": bookings_total,
        "bookings_today": bookings_today,
        "plan_free": plan_counts.get("free", 0),
        "plan_pro": plan_counts.get("pro", 0),
        "plan_premium": plan_counts.get("premium", 0),
        "partners": partners,
        "clients": clients,
        "partner_created_listings": partner_created,
        "partner_assigned_listings": partner_assigned,
        "enquiries_total": enquiry_stats["total"],
        "enquiries_open": enquiry_stats["open"],
        "industry_top": industry_top,
    }


def search_users(query="", limit=50):
    qs = (
        User.objects.select_related("profile", "profile__business")
        .order_by("-date_joined")
    )
    q = (query or "").strip()
    if q:
        qs = qs.filter(
            Q(email__icontains=q)
            | Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(profile__business__name__icontains=q)
            | Q(profile__phone__icontains=q)
        )
    return list(qs[:limit])


def get_user_detail(user_id):
    return (
        User.objects.select_related("profile", "profile__business")
        .filter(pk=user_id)
        .first()
    )


def ban_user(actor, target, request=None):
    if target.is_superuser:
        raise ValueError("Cannot ban a superuser.")
    if target.pk == actor.pk:
        raise ValueError("Cannot ban yourself.")
    target.is_active = False
    target.save(update_fields=["is_active"])
    log_admin_action(
        actor,
        "ban",
        f"Banned {target.email}",
        target_user=target,
        request=request,
    )
    return target


def unban_user(actor, target, request=None):
    target.is_active = True
    target.save(update_fields=["is_active"])
    log_admin_action(
        actor,
        "unban",
        f"Unbanned {target.email}",
        target_user=target,
        request=request,
    )
    return target


def start_impersonation(request, target):
    actor = request.user
    if target.pk == actor.pk:
        raise ValueError("Already this user.")
    if not actor.is_staff and not actor.is_superuser:
        raise ValueError("Staff only.")
    if target.is_superuser and not actor.is_superuser:
        raise ValueError("Cannot impersonate a superuser.")

    from django.contrib.auth import login

    request.session[IMPERSONATOR_SESSION_KEY] = actor.pk
    log_admin_action(
        actor,
        "impersonate",
        f"Started impersonating {target.email}",
        target_user=target,
        request=request,
    )
    login(request, target, backend="django.contrib.auth.backends.ModelBackend")
    # Keep impersonator id after login cycle
    request.session[IMPERSONATOR_SESSION_KEY] = actor.pk


def stop_impersonation(request):
    from django.contrib.auth import login

    impersonator_id = request.session.get(IMPERSONATOR_SESSION_KEY)
    if not impersonator_id:
        raise ValueError("Not impersonating.")
    actor = User.objects.filter(pk=impersonator_id).first()
    if not actor:
        request.session.pop(IMPERSONATOR_SESSION_KEY, None)
        raise ValueError("Original staff user missing.")

    target = request.user
    login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
    request.session.pop(IMPERSONATOR_SESSION_KEY, None)
    log_admin_action(
        actor,
        "stop_impersonate",
        f"Stopped impersonating {target.email}",
        target_user=target,
        request=request,
    )


def is_impersonating(request):
    return bool(request.session.get(IMPERSONATOR_SESSION_KEY))


def staff_or_superuser_check(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and user.is_active
        and (
            user.is_staff
            or user.is_superuser
            or getattr(user, "platform_role", None) == "super_admin"
        )
    )


def get_activity_feed(limit=30):
    """Merge AdminLog with recent platform events for the live feed."""
    from booking.models import Appointment

    items = []

    for row in AdminLog.objects.select_related("actor", "target_user")[:limit]:
        items.append(
            {
                "kind": "admin",
                "at": row.created_at,
                "title": row.get_action_display(),
                "detail": row.message,
                "actor": row.actor.email if row.actor_id else "system",
            }
        )

    for user in User.objects.order_by("-date_joined")[:10]:
        items.append(
            {
                "kind": "signup",
                "at": user.date_joined,
                "title": "New signup",
                "detail": user.email,
                "actor": "platform",
            }
        )

    for appt in Appointment.objects.select_related("business", "customer").order_by(
        "-created_at"
    )[:10]:
        items.append(
            {
                "kind": "booking",
                "at": appt.created_at,
                "title": "Booking",
                "detail": f"{appt.business.name} · {appt.customer.first_name} · {appt.date}",
                "actor": "platform",
            }
        )

    items.sort(key=lambda x: x["at"] or timezone.now(), reverse=True)
    return items[:limit]
