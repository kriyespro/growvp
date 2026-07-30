from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from leads.forms import EnquiryCreateForm, EnquiryReplyForm
from leads.services import (
    QUICK_REPLY_PRESETS,
    bulk_set_enquiry_status,
    create_enquiry,
    enquiries_for_user,
    partner_enquiry_stats,
    reply_to_enquiry,
    set_enquiry_status,
    user_can_access_enquiry,
)
from users.models import Business
from users.services import businesses_for_user, home_url_for_user


def _layout_for(user):
    if user.platform_role == "client":
        return "account"
    if user.platform_role == "marketing_partner":
        return "partner"
    if user.platform_role == "business":
        return "business"
    return "control"


def _inbox_filters(request):
    return {
        "status": (request.GET.get("status") or "").strip().lower(),
        "business_id": (request.GET.get("business") or "").strip(),
        "q": (request.GET.get("q") or "").strip(),
        "sort": (request.GET.get("sort") or "-updated_at").strip(),
    }


@login_required(login_url="/auth/login/")
@ensure_csrf_cookie
def inbox(request):
    if request.user.platform_role == "super_admin" or request.user.is_staff:
        pass
    elif request.user.platform_role not in (
        "client",
        "marketing_partner",
        "business",
    ):
        return redirect(home_url_for_user(request.user))

    filters = _inbox_filters(request)
    enquiries = enquiries_for_user(
        request.user,
        status=filters["status"],
        business_id=filters["business_id"] or None,
        q=filters["q"],
        sort=filters["sort"],
    )
    layout = _layout_for(request.user)
    is_htmx = bool(getattr(request, "htmx", False))

    listings = []
    stats = None
    if layout in ("partner", "business", "control"):
        listings = list(businesses_for_user(request.user).order_by("name")[:200])
    if layout == "partner":
        stats = partner_enquiry_stats(request.user)

    context = {
        "enquiries": enquiries,
        "layout": layout,
        "nav": "enquiries",
        "filters": filters,
        "listings": listings,
        "enquiry_stats": stats,
        "can_manage_status": layout in ("partner", "business", "control"),
        "csrf_input_html": f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">',
    }
    if is_htmx:
        return render(request, "partials/_enquiry_inbox.jinja", context)
    if layout == "partner":
        return render(request, "pages/partner/enquiries.jinja", context)
    return render(request, "pages/leads/inbox.jinja", context)


@login_required(login_url="/auth/login/")
@ensure_csrf_cookie
def thread(request, pk):
    from leads.models import Enquiry

    enquiry = get_object_or_404(
        Enquiry.objects.select_related("business", "client").prefetch_related(
            "messages__sender"
        ),
        pk=pk,
    )
    if not user_can_access_enquiry(request.user, enquiry):
        return redirect("leads_inbox")

    layout = _layout_for(request.user)
    error = None
    if request.method == "POST":
        form = EnquiryReplyForm(request.POST)
        if form.is_valid():
            try:
                reply_to_enquiry(
                    user=request.user, enquiry=enquiry, body=form.cleaned_data["body"]
                )
                return redirect("leads_thread", pk=enquiry.pk)
            except (PermissionError, ValueError) as exc:
                error = str(exc)
    else:
        form = EnquiryReplyForm()

    context = {
        "enquiry": enquiry,
        "messages": enquiry.messages.select_related("sender").all(),
        "form": form,
        "error": error,
        "layout": layout,
        "nav": "enquiries",
        "quick_replies": QUICK_REPLY_PRESETS
        if layout in ("partner", "business", "control")
        else (),
        "can_manage_status": layout in ("partner", "business", "control")
        or (layout == "account" and enquiry.client_id == request.user.id),
    }
    if layout == "partner":
        return render(request, "pages/partner/enquiry_thread.jinja", context)
    return render(request, "pages/leads/thread.jinja", context)


@login_required(login_url="/auth/login/")
@require_POST
def enquiry_set_status(request, pk):
    from leads.models import Enquiry

    enquiry = get_object_or_404(Enquiry, pk=pk)
    try:
        set_enquiry_status(
            user=request.user,
            enquiry=enquiry,
            status=request.POST.get("status", ""),
        )
    except (PermissionError, ValueError):
        pass
    next_url = request.POST.get("next") or reverse("leads_thread", kwargs={"pk": pk})
    return redirect(next_url)


@login_required(login_url="/auth/login/")
@require_POST
def enquiry_bulk_status(request):
    try:
        updated = bulk_set_enquiry_status(
            user=request.user,
            ids=request.POST.getlist("ids"),
            status=request.POST.get("status", ""),
        )
    except ValueError:
        updated = 0
    qs = request.META.get("HTTP_REFERER") or reverse("leads_inbox")
    sep = "&" if "?" in qs else "?"
    return redirect(f"{qs}{sep}bulk={updated}")


@ensure_csrf_cookie
def create_for_business(request, business_slug):
    business = get_object_or_404(Business, slug=business_slug)
    next_path = f"/leads/new/{business.slug}/"
    product_id = (request.GET.get("product") or "").strip()
    if product_id:
        next_path = f"{next_path}?product={product_id}"
    if not request.user.is_authenticated:
        return redirect(f"/auth/login/?next={next_path}")
    if request.user.platform_role != "client":
        return redirect(f"/auth/register/?as=client&next={next_path}")

    product = None
    if product_id.isdigit():
        from catalog.models import Product

        product = Product.objects.filter(
            id=int(product_id), business=business, is_active=True
        ).first()

    error = None
    if request.method == "POST":
        form = EnquiryCreateForm(request.POST)
        if form.is_valid():
            try:
                enquiry = create_enquiry(
                    client=request.user,
                    business=business,
                    subject=form.cleaned_data.get("subject") or "",
                    body=form.cleaned_data["body"],
                )
                return redirect("leads_thread", pk=enquiry.pk)
            except ValueError as exc:
                error = str(exc)
    else:
        initial = {}
        if product:
            initial["subject"] = f"Enquiry about {product.name}"
            initial["body"] = (
                f"Hi, I'm interested in “{product.name}” (₹{product.price}). "
                f"Please share availability / details."
            )
        form = EnquiryCreateForm(initial=initial)

    return render(
        request,
        "pages/leads/create.jinja",
        {
            "business": business,
            "product": product,
            "form": form,
            "error": error,
            "layout": "account",
            "nav": "enquiries",
        },
    )
