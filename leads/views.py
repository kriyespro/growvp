from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from leads.forms import EnquiryCreateForm, EnquiryReplyForm
from leads.services import (
    create_enquiry,
    enquiries_for_user,
    reply_to_enquiry,
    user_can_access_enquiry,
)
from users.models import Business
from users.services import home_url_for_user


def _layout_for(user):
    if user.platform_role == "client":
        return "account"
    if user.platform_role == "marketing_partner":
        return "partner"
    if user.platform_role == "business":
        return "business"
    return "control"


@login_required(login_url="/auth/login/")
@ensure_csrf_cookie
def inbox(request):
    if request.user.platform_role == "super_admin" or request.user.is_staff:
        # Super admin can browse all, but prefer mission control
        pass
    elif request.user.platform_role not in (
        "client",
        "marketing_partner",
        "business",
    ):
        return redirect(home_url_for_user(request.user))

    enquiries = enquiries_for_user(request.user)
    layout = _layout_for(request.user)
    is_htmx = bool(getattr(request, "htmx", False))
    context = {
        "enquiries": enquiries,
        "layout": layout,
        "nav": "enquiries",
        "csrf_input_html": f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">',
    }
    if is_htmx and layout == "business":
        return render(request, "partials/_business_enquiries_panel.jinja", context)
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

    return render(
        request,
        "pages/leads/thread.jinja",
        {
            "enquiry": enquiry,
            "messages": enquiry.messages.select_related("sender").all(),
            "form": form,
            "error": error,
            "layout": _layout_for(request.user),
            "nav": "enquiries",
        },
    )


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
