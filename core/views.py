from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def landing(request):
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('dashboard')
    return render(request, 'pages/landing.jinja')


@ensure_csrf_cookie
def business_landing(request, business_slug):
    from django.shortcuts import get_object_or_404
    from users.models import Business
    from catalog.models import Service

    business = get_object_or_404(Business, slug=business_slug)
    services = Service.objects.filter(category__business=business, is_active=True).select_related('category').order_by('category__name', 'name')
    return render(request, 'pages/public/business_landing.jinja', {'business': business, 'services': services})

@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def dashboard(request):
    try:
        profile = getattr(request.user, 'profile', None)
    except Exception:
        profile = None
    
    if not profile:
        from django.contrib.auth import logout
        from django.shortcuts import redirect
        logout(request)
        return redirect('landing')
    if not profile.business.is_profile_ready:
        from django.shortcuts import redirect
        return redirect('/auth/business-profile/?onboarding=1')

    context = {
        'business': profile.business,
        'role': profile.role
    }
    return render(request, 'pages/dashboard.jinja', context)

@login_required(login_url='/auth/login/')
def dashboard_home(request):
    try:
        profile = getattr(request.user, 'profile', None)
    except Exception:
        profile = None
    
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)

    business = profile.business
    
    import datetime
    from django.utils import timezone
    from booking.models import Appointment
    from crm.models import Customer
    from billing.models import Invoice
    from django.db.models import Sum
    
    today = timezone.now().date()
    
    # Today's Revenue
    today_revenue = Invoice.objects.filter(
        business=business, 
        status='paid',
        created_at__date=today
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    
    # Appointments Today
    today_appointments = Appointment.objects.filter(
        business=business,
        date=today
    ).count()
    
    # Total Clients
    total_clients = Customer.objects.filter(business=business).count()
    
    # No Shows
    total_appointments = Appointment.objects.filter(business=business).count()
    no_shows = Appointment.objects.filter(business=business, status='no-show').count()
    no_show_rate = int((no_shows / total_appointments) * 100) if total_appointments > 0 else 0
    
    context = {
        'business': business,
        'today_revenue': today_revenue,
        'today_revenue_display': f"{today_revenue:.2f}",
        'today_appointments': today_appointments,
        'total_clients': total_clients,
        'no_show_rate': no_show_rate,
    }
    return render(request, 'partials/_dashboard_home.jinja', context)
