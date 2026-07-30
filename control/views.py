from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
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
def businesses_import(request):
    from users.forms import ListingImportForm
    from users.listing_import import (
        IMPORT_COLUMNS,
        import_listing_rows,
        load_rows_from_source,
    )

    form = ListingImportForm()
    result = None
    error = None
    if request.method == "POST":
        form = ListingImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                headers, body = load_rows_from_source(
                    uploaded_file=form.cleaned_data.get("file"),
                    google_sheet_url=form.cleaned_data.get("google_sheet_url") or "",
                )
                result = import_listing_rows(
                    request.user,
                    headers,
                    body,
                    allow_paid_plans=True,
                    owner=form.cleaned_data.get("partner") or request.user,
                )
                services.log_admin_action(
                    request.user,
                    "other",
                    (
                        f"Imported listings: {result.created_count} created, "
                        f"{result.error_count} errors"
                    ),
                    request=request,
                )
                form = ListingImportForm()
            except ValueError as exc:
                error = str(exc)
    return render(
        request,
        "control/businesses_import.jinja",
        _control_context(
            request,
            nav="businesses",
            form=form,
            result=result,
            error=error,
            columns=IMPORT_COLUMNS,
        ),
    )


@control_login_required
@require_GET
def businesses_import_sample(request):
    from users.listing_import import build_sample_csv, build_sample_xlsx

    fmt = (request.GET.get("format") or "csv").strip().lower()
    if fmt in ("xlsx", "excel", "xls"):
        data = build_sample_xlsx()
        return HttpResponse(
            data,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": (
                    'attachment; filename="suratbazar-listings-sample.xlsx"'
                ),
            },
        )
    data = build_sample_csv()
    return HttpResponse(
        data,
        content_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="suratbazar-listings-sample.csv"'
            ),
        },
    )


@control_login_required
@require_GET
def partner_listings(request):
    from leads.services import list_marketing_partners

    q = (request.GET.get("q") or "").strip()
    partner_id = request.GET.get("partner") or ""
    partner_pk = int(partner_id) if str(partner_id).isdigit() else None
    qs = services.partner_listings_queryset(q=q, partner_id=partner_pk)
    return render(
        request,
        "control/partner_listings.jinja",
        _control_context(
            request,
            nav="partner_listings",
            businesses=list(qs[:300]),
            total_count=qs.count(),
            q=q,
            partner_id=partner_pk or "",
            partners=list(list_marketing_partners()),
            deleted=request.GET.get("deleted"),
            saved=request.GET.get("saved"),
        ),
    )


@control_login_required
@require_GET
def partner_listings_export(request):
    from users.listing_import import export_listings_csv, export_listings_xlsx

    q = (request.GET.get("q") or "").strip()
    partner_id = request.GET.get("partner") or ""
    partner_pk = int(partner_id) if str(partner_id).isdigit() else None
    ids = request.GET.getlist("id")
    qs = services.partner_listings_queryset(q=q, partner_id=partner_pk)
    if ids:
        id_ints = [int(i) for i in ids if str(i).isdigit()]
        qs = qs.filter(pk__in=id_ints)
    businesses = list(qs[:2000])
    fmt = (request.GET.get("format") or "csv").strip().lower()
    if fmt in ("xlsx", "excel", "xls"):
        data = export_listings_xlsx(businesses)
        return HttpResponse(
            data,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": (
                    'attachment; filename="partner-listings-export.xlsx"'
                ),
            },
        )
    data = export_listings_csv(businesses)
    return HttpResponse(
        data,
        content_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="partner-listings-export.csv"'
            ),
        },
    )


@control_login_required
def partner_listings_import(request):
    from leads.services import list_marketing_partners
    from users.forms import ListingImportForm
    from users.listing_import import (
        IMPORT_COLUMNS,
        import_listing_rows,
        load_rows_from_source,
    )

    form = ListingImportForm()
    result = None
    error = None
    if request.method == "POST":
        form = ListingImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                headers, body = load_rows_from_source(
                    uploaded_file=form.cleaned_data.get("file"),
                    google_sheet_url=form.cleaned_data.get("google_sheet_url") or "",
                )
                owner = form.cleaned_data.get("partner") or request.user
                result = import_listing_rows(
                    request.user,
                    headers,
                    body,
                    allow_paid_plans=True,
                    owner=owner,
                )
                services.log_admin_action(
                    request.user,
                    "other",
                    (
                        f"Partner listings import: {result.created_count} created, "
                        f"{result.error_count} errors"
                    ),
                    request=request,
                )
                form = ListingImportForm()
            except ValueError as exc:
                error = str(exc)
    return render(
        request,
        "control/partner_listings_import.jinja",
        _control_context(
            request,
            nav="partner_listings",
            form=form,
            result=result,
            error=error,
            columns=IMPORT_COLUMNS,
            partners=list(list_marketing_partners()),
        ),
    )


@control_login_required
@require_POST
def partner_listings_bulk_delete(request):
    ids = request.POST.getlist("ids")
    deleted = services.bulk_delete_partner_listings(
        request.user, ids, request=request
    )
    return redirect(f"{reverse('control:partner_listings')}?deleted={deleted}")


@control_login_required
@require_GET
def dummy_data(request):
    preview = services.get_dummy_data_preview(exclude_user_id=request.user.pk)
    return render(
        request,
        "control/dummy_data.jinja",
        {
            "nav": "dummy_data",
            **preview,
            "error": request.GET.get("error", ""),
            "purged_b": request.GET.get("purged_b", ""),
            "purged_u": request.GET.get("purged_u", ""),
        },
    )


@control_login_required
@require_POST
def dummy_data_purge(request):
    scope = (request.POST.get("scope") or "all").strip()
    selected = request.POST.getlist("ids") if scope == "selected" else None
    try:
        result = services.purge_dummy_data(
            request.user,
            confirm_phrase=request.POST.get("confirm_phrase", ""),
            delete_businesses=request.POST.get("delete_businesses") == "1",
            delete_users=request.POST.get("delete_users") == "1",
            selected_ids=selected,
            request=request,
        )
    except ValueError as exc:
        from urllib.parse import quote

        return redirect(
            f"{reverse('control:dummy_data')}?error={quote(str(exc))}"
        )
    return redirect(
        f"{reverse('control:dummy_data')}"
        f"?purged_b={result['businesses_deleted']}"
        f"&purged_u={result['users_deleted']}"
    )


@control_login_required
def partner_listing_edit(request, pk):
    from core.services import bust_directory_cache
    from users.forms import ControlBusinessEditForm

    business = get_object_or_404(services.partner_listings_queryset(), pk=pk)
    if request.method == "POST":
        form = ControlBusinessEditForm(request.POST, instance=business)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.public_phone and updated.public_address:
                updated.profile_setup_completed = True
            updated.save()
            bust_directory_cache()
            services.log_admin_action(
                request.user,
                "other",
                f"Edited partner listing {updated.name}",
                request=request,
            )
            return redirect(f"{reverse('control:partner_listings')}?saved=1")
    else:
        form = ControlBusinessEditForm(instance=business)
    return render(
        request,
        "control/partner_listing_edit.jinja",
        _control_context(
            request,
            nav="partner_listings",
            form=form,
            business=business,
        ),
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
