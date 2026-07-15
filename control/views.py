from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from control.access import control_login_required
from control import services

User = get_user_model()


def _control_context(request, **extra):
    ctx = {
        "request": request,
        "is_impersonating": services.is_impersonating(request),
        "nav": extra.pop("nav", "dashboard"),
    }
    ctx.update(extra)
    return ctx


@control_login_required
@require_GET
def dashboard(request):
    return render(
        request,
        "control/dashboard.jinja",
        _control_context(
            request,
            nav="dashboard",
            stats=services.get_dashboard_stats(),
            activity=services.get_activity_feed(limit=12),
        ),
    )


@control_login_required
@require_GET
def stats_partial(request):
    return render(
        request,
        "control/partials/_stats_cards.jinja",
        {"stats": services.get_dashboard_stats()},
    )


@control_login_required
@require_GET
def activity_partial(request):
    return render(
        request,
        "control/partials/_activity_feed.jinja",
        {"activity": services.get_activity_feed(limit=20)},
    )


@control_login_required
@require_GET
def users_list(request):
    q = request.GET.get("q", "")
    users = services.search_users(q)
    template = (
        "control/partials/_user_rows.jinja"
        if request.headers.get("HX-Request")
        else "control/users.jinja"
    )
    return render(
        request,
        template,
        _control_context(request, nav="users", users=users, q=q),
    )


@control_login_required
@require_GET
def user_detail(request, pk):
    user = get_object_or_404(
        User.objects.select_related("profile", "profile__business"),
        pk=pk,
    )
    return render(
        request,
        "control/user_detail.jinja",
        _control_context(request, nav="users", target=user),
    )


@control_login_required
@require_POST
def user_ban(request, pk):
    target = get_object_or_404(User, pk=pk)
    try:
        services.ban_user(request.user, target, request=request)
    except ValueError as exc:
        return HttpResponseForbidden(str(exc))
    if request.headers.get("HX-Request"):
        return render(
            request,
            "control/partials/_user_row.jinja",
            {"user": target},
        )
    return redirect("control:user_detail", pk=pk)


@control_login_required
@require_POST
def user_unban(request, pk):
    target = get_object_or_404(User, pk=pk)
    try:
        services.unban_user(request.user, target, request=request)
    except ValueError as exc:
        return HttpResponseForbidden(str(exc))
    if request.headers.get("HX-Request"):
        return render(
            request,
            "control/partials/_user_row.jinja",
            {"user": target},
        )
    return redirect("control:user_detail", pk=pk)


@control_login_required
@require_POST
def impersonate(request, pk):
    from users.services import home_url_for_user

    target = get_object_or_404(User, pk=pk)
    try:
        services.start_impersonation(request, target)
    except ValueError as exc:
        return HttpResponseForbidden(str(exc))
    return redirect(home_url_for_user(target))


@require_POST
def stop_impersonate(request):
    """Allowed while impersonating even if the current user is not staff."""
    if not services.is_impersonating(request) and not services.staff_or_superuser_check(request.user):
        return redirect("/auth/login/?next=/admin/")
    try:
        services.stop_impersonation(request)
    except ValueError as exc:
        return HttpResponse(str(exc), status=400)
    return redirect("control:dashboard")


@control_login_required
@require_GET
def activity_page(request):
    return render(
        request,
        "control/activity.jinja",
        _control_context(
            request,
            nav="activity",
            activity=services.get_activity_feed(limit=40),
        ),
    )


@control_login_required
@require_GET
def businesses_list(request):
    from users.models import Business

    q = (request.GET.get("q") or "").strip()
    qs = Business.objects.select_related("created_by").prefetch_related(
        "assigned_partners"
    ).order_by("-created_at")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
    return render(
        request,
        "control/businesses.jinja",
        _control_context(request, nav="businesses", businesses=list(qs[:100]), q=q),
    )


@control_login_required
@require_GET
def partners_list(request):
    from users.models import Business
    from leads.services import list_marketing_partners

    partners = list(list_marketing_partners())
    businesses = list(Business.objects.order_by("name")[:200])
    return render(
        request,
        "control/partners.jinja",
        _control_context(
            request,
            nav="partners",
            partners=partners,
            businesses=businesses,
        ),
    )


@control_login_required
@require_POST
def partner_assign(request):
    from users.models import Business
    from users.services import assign_partner_to_business

    partner = get_object_or_404(User, pk=request.POST.get("partner_id"))
    business = get_object_or_404(Business, pk=request.POST.get("business_id"))
    try:
        assign_partner_to_business(partner, business)
        services.log_admin_action(
            request.user,
            "other",
            f"Assigned partner {partner.email} to {business.name}",
            target_user=partner,
            request=request,
        )
    except ValueError as exc:
        return HttpResponseForbidden(str(exc))
    return redirect("control:partners")


@control_login_required
@require_POST
def partner_unassign(request):
    from users.models import Business
    from users.services import unassign_partner_from_business

    partner = get_object_or_404(User, pk=request.POST.get("partner_id"))
    business = get_object_or_404(Business, pk=request.POST.get("business_id"))
    unassign_partner_from_business(partner, business)
    services.log_admin_action(
        request.user,
        "other",
        f"Unassigned partner {partner.email} from {business.name}",
        target_user=partner,
        request=request,
    )
    return redirect("control:partners")
