from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from .models import Service, ServiceCategory, Product
from .forms import ServiceForm, ServiceCategoryForm, ProductForm
from .services import get_business_hours, update_business_hours_from_post
from core.services import bust_directory_cache
from core.plans import (
    PLAN_CONFIG,
    can_add_product,
    can_add_service,
    get_plan_config,
    plan_allows_products,
    remaining_product_slots,
    remaining_service_slots,
)

@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def services_list(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)
        
    business = profile.business
    services = Service.objects.filter(category__business=business).select_related('category')
    
    edit_id = request.GET.get('edit')
    editing_service = None
    if edit_id:
        editing_service = Service.objects.filter(
            id=edit_id,
            category__business=business
        ).select_related('category').first()

    if request.method == 'POST':
        if editing_service:
            form = ServiceForm(
                request.POST,
                request.FILES,
                business=business,
                instance=editing_service
            )
            if form.is_valid():
                form.save()
                bust_directory_cache()
                editing_service = None
                form = ServiceForm(business=business)
        else:
            form = ServiceForm(request.POST, request.FILES, business=business)
            if form.is_valid():
                form.save()
                bust_directory_cache()
                form = ServiceForm(business=business)
    else:
        if editing_service:
            form = ServiceForm(business=business, instance=editing_service)
        else:
            form = ServiceForm(business=business)
        
    context = {
        'services': services,
        'form': form,
        'categories_exist': ServiceCategory.objects.filter(business=business).exists(),
        'editing_service': editing_service,
        'plan': get_plan_config(business.listing_plan),
        'can_add_service': can_add_service(business),
        'remaining_service_slots': remaining_service_slots(business),
    }
    return render(request, 'pages/catalog/services_list.jinja', context)


@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def delete_service(request, service_id):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)

    if request.method == 'POST':
        service = get_object_or_404(
            Service,
            id=service_id,
            category__business=profile.business
        )
        service.delete()
        bust_directory_cache()
    return services_list(request)

@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def categories_list(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)
        
    business = profile.business
    categories = ServiceCategory.objects.filter(business=business)
    
    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.business = business
            cat.save()
            form = ServiceCategoryForm()
    else:
        form = ServiceCategoryForm()
        
    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'pages/catalog/categories_list.jinja', context)


@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
@require_http_methods(['GET', 'POST'])
def business_hours(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)

    business = profile.business
    saved = False
    if request.method == 'POST':
        hours = update_business_hours_from_post(business, request.POST)
        saved = True
        bust_directory_cache()
    else:
        hours = get_business_hours(business)

    context = {
        'business': business,
        'hours': hours,
        'saved': saved,
        'onboarding_mode': request.GET.get('onboarding') == '1',
    }
    return render(request, 'partials/_business_hours_editor.jinja', context)


@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def products_list(request):
    from django.http import HttpResponse

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.business_id:
        return HttpResponse(
            '<div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">'
            'No business linked. Complete profile setup first.'
            '</div>',
            status=400,
        )

    business = profile.business
    products = Product.objects.filter(business=business).order_by('name')
    edit_id = request.GET.get('edit')
    editing_product = None
    if edit_id:
        editing_product = Product.objects.filter(id=edit_id, business=business).first()

    form_error = None
    if request.method == 'POST':
        if editing_product:
            form = ProductForm(
                request.POST,
                request.FILES,
                business=business,
                instance=editing_product,
            )
            if form.is_valid():
                form.save()
                editing_product = None
                form = ProductForm(business=business)
            else:
                form_error = form.errors
        else:
            form = ProductForm(request.POST, request.FILES, business=business)
            if form.is_valid():
                product = form.save(commit=False)
                product.business = business
                product.save()
                form = ProductForm(business=business)
            else:
                form_error = form.errors
    else:
        if editing_product:
            form = ProductForm(business=business, instance=editing_product)
        else:
            form = ProductForm(business=business)

    plan = get_plan_config(business.listing_plan)
    context = {
        'business': business,
        'products': products,
        'form': form,
        'editing_product': editing_product,
        'form_error': form_error,
        'plan': plan,
        'products_enabled': plan_allows_products(business.listing_plan),
        'can_add_product': can_add_product(business),
        'remaining_slots': remaining_product_slots(business),
    }
    return render(request, 'pages/catalog/products_list.jinja', context)


@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def delete_product(request, product_id):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)

    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, business=profile.business)
        product.delete()
    return products_list(request)
