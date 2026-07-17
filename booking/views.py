from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Appointment
from .forms import AppointmentForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q

@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def calendar_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)
        
    business = profile.business
    appointments = (
        Appointment.objects.filter(business=business)
        .select_related('customer', 'service')
        .order_by('-date', '-start_time')[:200]
    )
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, business=business)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.business = business
            appt.save()
            form = AppointmentForm(business=business)
    else:
        form = AppointmentForm(business=business)
        
    context = {
        'appointments': appointments,
        'form': form,
    }
    return render(request, 'pages/booking/calendar.jinja', context)

from users.models import Business
from catalog.models import Service
from crm.models import Customer
from core.plans import plan_hides_platform_branding

@ensure_csrf_cookie
def public_booking(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    return _public_booking(request, business)


@ensure_csrf_cookie
def public_booking_by_slug(request, business_slug):
    business = get_object_or_404(Business, slug=business_slug)
    return _public_booking(request, business)


def _public_booking(request, business):
    services = Service.objects.filter(category__business=business, is_active=True)
    error_message = None

    if request.method == 'POST':
        service_id = request.POST.get('service')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        phone = request.POST.get('phone')
        first_name = request.POST.get('first_name')

        if service_id and date_str and time_str and phone and first_name:
            service = get_object_or_404(Service, id=service_id, category__business=business)

            try:
                start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                error_message = "Please select a valid date and time."
            else:
                end_dt = start_dt + timedelta(minutes=service.duration_mins)
                has_overlap = Appointment.objects.filter(
                    business=business,
                    date=start_dt.date(),
                ).filter(
                    Q(start_time__lt=end_dt.time()) & Q(end_time__gt=start_dt.time())
                ).exists()
                if has_overlap:
                    error_message = "This slot is already booked. Please choose another time."
                else:
                    customer, _ = Customer.objects.get_or_create(
                        business=business,
                        phone=phone,
                        defaults={'first_name': first_name}
                    )
                    if customer.first_name != first_name:
                        customer.first_name = first_name
                        customer.save(update_fields=['first_name'])
                    Appointment.objects.create(
                        business=business,
                        customer=customer,
                        service=service,
                        date=start_dt.date(),
                        start_time=start_dt.time(),
                        end_time=end_dt.time(),
                        status='confirmed'
                    )
                    return render(
                        request,
                        'pages/public/booking_success.jinja',
                        {
                            'business': business,
                            'hide_platform_branding': plan_hides_platform_branding(
                                business.listing_plan
                            ),
                        },
                    )
        else:
            error_message = "Please fill all required fields."

    selected_service_id = request.GET.get('service') or request.POST.get('service')
    try:
        selected_service_id = int(selected_service_id) if selected_service_id else None
    except (TypeError, ValueError):
        selected_service_id = None

    return render(request, 'pages/public/booking.jinja', {
        'business': business,
        'services': services,
        'selected_service_id': selected_service_id,
        'error_message': error_message,
        'hide_platform_branding': plan_hides_platform_branding(business.listing_plan),
    })
