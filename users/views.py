from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, BusinessLandingForm
from .models import User, Business, UserProfile
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.utils.http import url_has_allowed_host_and_scheme

@ensure_csrf_cookie
def register_business(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create Business
            business = Business.objects.create(
                name=form.cleaned_data['business_name'],
                industry_type=form.cleaned_data['industry_type']
            )
            
            # Create User
            user = User.objects.create_user(
                username=form.cleaned_data['email'], # AbstractUser needs username
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            
            # Create Profile
            UserProfile.objects.create(
                user=user,
                business=business,
                role='admin'
            )
            
            # Login immediately
            login(request, user)
            
            if request.htmx:
                # If HTMX request, we can trigger client-side redirect
                response = render(request, 'partials/_redirect.jinja')
                response['HX-Redirect'] = '/dashboard/'
                return response
            return redirect('/dashboard/')
            
    else:
        form = RegistrationForm()
        
    return render(request, 'pages/register.jinja', {'form': form})


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/dashboard/')
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = '/dashboard/'
            return redirect(next_url)
        else:
            error = 'Invalid email or password.'
    
    context = {
        'error': error,
        'csrf_input_html': f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">',
    }
    return render(request, 'pages/login.jinja', context)


@require_http_methods(['POST', 'GET'])
def logout_view(request):
    logout(request)
    return redirect('/')


@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def business_profile(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)

    business = profile.business
    if request.method == 'POST':
        form = BusinessLandingForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            form = BusinessLandingForm(instance=business)
    else:
        form = BusinessLandingForm(instance=business)

    context = {
        'form': form,
        'business': business,
    }
    return render(request, 'pages/business_profile.jinja', context)
