from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from django.middleware.csrf import get_token
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import HttpResponse

from catalog.services import (
    ensure_starter_categories,
    ensure_default_hours,
    get_listing_readiness,
    get_business_hours,
)
from core.plans import PLAN_CONFIG, get_plan_config, plan_allows_website
from core.services import bust_directory_cache
from users.forms import (
    RegistrationForm,
    SimpleAccountForm,
    BusinessLandingForm,
    ListingPlanForm,
    PartnerListingForm,
)
from users.models import User, Business, UserProfile
from users.services import home_url_for_user, create_partner_listing, businesses_for_partner
from users.access import require_platform_role, assert_can_manage_business


@ensure_csrf_cookie
def register_business(request):
    role_as = (request.GET.get("as") or "business").strip().lower()
    if role_as == "partner":
        return register_partner(request)
    if role_as == "client":
        return register_client(request)

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            business = Business.objects.create(
                name=form.cleaned_data["business_name"],
                industry_type=form.cleaned_data["industry_type"],
                public_phone=form.cleaned_data["public_phone"],
                timezone="Asia/Kolkata",
            )

            user = User.objects.create_user(
                username=form.cleaned_data["email"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                platform_role="business",
            )
            business.created_by = user
            business.save(update_fields=["created_by"])

            UserProfile.objects.create(
                user=user,
                business=business,
                role="admin",
                phone=form.cleaned_data["public_phone"],
            )
            ensure_starter_categories(business)
            ensure_default_hours(business)

            login(request, user)

            if getattr(request, "htmx", False):
                response = render(request, "partials/_redirect.jinja")
                response["HX-Redirect"] = "/auth/business-profile/?onboarding=1"
                return response
            return redirect("/auth/business-profile/?onboarding=1")
    else:
        form = RegistrationForm()

    return render(
        request,
        "pages/register.jinja",
        {"form": form, "register_as": "business"},
    )


@ensure_csrf_cookie
def register_partner(request):
    if request.method == "POST":
        form = SimpleAccountForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["email"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                platform_role="marketing_partner",
            )
            login(request, user)
            return redirect("/partner/")
    else:
        form = SimpleAccountForm()
    return render(
        request,
        "pages/register_simple.jinja",
        {
            "form": form,
            "register_as": "partner",
            "title": "Join as marketing partner",
            "subtitle": "Create listings for local businesses and manage their enquiries.",
            "submit_label": "Create partner account",
            "post_url": "/auth/register/?as=partner",
        },
    )


@ensure_csrf_cookie
def register_client(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "/account/"
    if request.method == "POST":
        form = SimpleAccountForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["email"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                platform_role="client",
            )
            login(request, user)
            if not url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                next_url = "/account/"
            return redirect(next_url)
    else:
        form = SimpleAccountForm()
    return render(
        request,
        "pages/register_simple.jinja",
        {
            "form": form,
            "register_as": "client",
            "title": "Create client account",
            "subtitle": "Send enquiries to local businesses and track replies.",
            "submit_label": "Create client account",
            "post_url": "/auth/register/?as=client",
            "next_url": next_url,
        },
    )


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect(home_url_for_user(request.user))

    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            profile = getattr(user, "profile", None)
            if (
                user.platform_role == "business"
                and profile
                and profile.business_id
            ):
                ensure_starter_categories(profile.business)
                ensure_default_hours(profile.business)
                if not profile.business.is_profile_ready:
                    return redirect("/auth/business-profile/?onboarding=1")
            default_home = home_url_for_user(user)
            next_url = request.GET.get("next", default_home)
            if not url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                next_url = default_home
            return redirect(next_url)
        error = "Invalid email or password."

    context = {
        "error": error,
        "csrf_input_html": f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">',
    }
    return render(request, "pages/login.jinja", context)


@require_http_methods(["POST", "GET"])
def logout_view(request):
    logout(request)
    return redirect("/")


@login_required(login_url="/auth/login/")
@ensure_csrf_cookie
def business_profile(request):
    profile = getattr(request.user, "profile", None)
    if not profile or not profile.business_id:
        return HttpResponse("Unauthorized", status=401)

    business = profile.business
    ensure_default_hours(business)
    saved = False
    onboarding_mode = request.GET.get("onboarding") == "1"
    is_htmx = bool(getattr(request, "htmx", False))

    if request.method == "POST":
        form = BusinessLandingForm(request.POST, instance=business)
        if form.is_valid():
            updated_business = form.save(commit=False)
            updated_business.profile_setup_completed = True
            updated_business.save()
            business = updated_business
            saved = True
            bust_directory_cache()
            if onboarding_mode:
                if is_htmx:
                    response = render(
                        request,
                        "partials/_redirect.jinja",
                        {"message": "Profile saved! Opening your dashboard…"},
                    )
                    response["HX-Redirect"] = "/dashboard/?setup=1"
                    return response
                return redirect("/dashboard/?setup=1")
            form = BusinessLandingForm(instance=business)
    else:
        form = BusinessLandingForm(instance=business)

    context = {
        "form": form,
        "business": business,
        "hours": get_business_hours(business),
        "onboarding_mode": onboarding_mode,
        "dashboard_embed": is_htmx and not onboarding_mode,
        "saved": saved,
        "readiness": get_listing_readiness(business),
        "website_enabled": plan_allows_website(business.listing_plan),
        "plan": get_plan_config(business.listing_plan),
        "csrf_input_html": f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">',
    }

    if is_htmx and not onboarding_mode:
        return render(request, "partials/_business_profile_content.jinja", context)
    return render(request, "pages/business_profile.jinja", context)


@login_required(login_url="/auth/login/")
@ensure_csrf_cookie
def listing_plans(request):
    profile = getattr(request.user, "profile", None)
    if not profile or not profile.business_id:
        return HttpResponse("Unauthorized", status=401)

    business = profile.business
    saved = False
    if request.method == "POST":
        form = ListingPlanForm(request.POST)
        if form.is_valid():
            business.listing_plan = form.cleaned_data["listing_plan"]
            business.save(update_fields=["listing_plan"])
            saved = True
            bust_directory_cache()
    else:
        form = ListingPlanForm(initial={"listing_plan": business.listing_plan})

    is_htmx = bool(getattr(request, "htmx", False))
    context = {
        "business": business,
        "form": form,
        "saved": saved,
        "plans": PLAN_CONFIG,
        "current_plan": get_plan_config(business.listing_plan),
        "dashboard_embed": is_htmx,
        "csrf_input_html": f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">',
    }
    template = (
        "partials/_listing_plans.jinja" if is_htmx else "pages/listing_plans.jinja"
    )
    return render(request, template, context)


# --- Partner dashboard ---


@require_platform_role("marketing_partner")
@ensure_csrf_cookie
def partner_home(request):
    from leads.services import partner_enquiry_stats

    listings = businesses_for_partner(request.user)
    stats = partner_enquiry_stats(request.user)
    return render(
        request,
        "pages/partner/home.jinja",
        {
            "listings": listings,
            "listing_count": listings.count(),
            "enquiry_stats": stats,
            "nav": "home",
        },
    )


@require_platform_role("marketing_partner")
@ensure_csrf_cookie
def partner_listings(request):
    return render(
        request,
        "pages/partner/listings.jinja",
        {
            "listings": businesses_for_partner(request.user),
            "nav": "listings",
        },
    )


@require_platform_role("marketing_partner")
@ensure_csrf_cookie
def partner_listing_create(request):
    from catalog.services import ensure_starter_categories, ensure_default_hours

    error = None
    if request.method == "POST":
        form = PartnerListingForm(request.POST)
        if form.is_valid():
            business = create_partner_listing(
                request.user,
                name=form.cleaned_data["name"],
                industry_type=form.cleaned_data["industry_type"],
                public_phone=form.cleaned_data.get("public_phone") or "",
            )
            ensure_starter_categories(business)
            ensure_default_hours(business)
            return redirect("partner_listing_edit", pk=business.pk)
    else:
        form = PartnerListingForm()
    return render(
        request,
        "pages/partner/listing_create.jinja",
        {"form": form, "error": error, "nav": "listings"},
    )


@require_platform_role("marketing_partner")
@ensure_csrf_cookie
def partner_listing_edit(request, pk):
    business = get_object_or_404(Business, pk=pk)
    assert_can_manage_business(request.user, business)
    ensure_default_hours(business)
    saved = False
    if request.method == "POST":
        form = BusinessLandingForm(request.POST, instance=business)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.profile_setup_completed = True
            updated.save()
            business = updated
            saved = True
            bust_directory_cache()
            form = BusinessLandingForm(instance=business)
    else:
        form = BusinessLandingForm(instance=business)
    return render(
        request,
        "pages/partner/listing_edit.jinja",
        {
            "form": form,
            "business": business,
            "saved": saved,
            "website_enabled": plan_allows_website(business.listing_plan),
            "plan": get_plan_config(business.listing_plan),
            "nav": "listings",
            "csrf_input_html": f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">',
        },
    )


# --- Client account ---


@require_platform_role("client")
@ensure_csrf_cookie
def client_home(request):
    from leads.services import enquiries_for_user

    enquiries = list(enquiries_for_user(request.user)[:20])
    return render(
        request,
        "pages/account/home.jinja",
        {"enquiries": enquiries, "nav": "home"},
    )
