from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Service, ServiceCategory
from .forms import ServiceForm, ServiceCategoryForm

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
                editing_service = None
                form = ServiceForm(business=business)
        else:
            form = ServiceForm(request.POST, request.FILES, business=business)
            if form.is_valid():
                form.save()
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
