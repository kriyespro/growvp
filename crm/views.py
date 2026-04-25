from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Customer
from .forms import CustomerForm
from django.views.decorators.csrf import ensure_csrf_cookie

@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def customers_list(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)
        
    business = profile.business
    customers = Customer.objects.filter(business=business).order_by('-created_at')
    
    edit_id = request.GET.get('edit')
    editing_customer = None
    if edit_id:
        editing_customer = Customer.objects.filter(
            id=edit_id,
            business=business
        ).first()

    if request.method == 'POST':
        if editing_customer:
            form = CustomerForm(request.POST, instance=editing_customer)
            if form.is_valid():
                customer = form.save(commit=False)
                customer.business = business
                customer.save()
                form = CustomerForm()
                editing_customer = None
        else:
            form = CustomerForm(request.POST)
            if form.is_valid():
                phone = form.cleaned_data['phone']
                customer = Customer.objects.filter(business=business, phone=phone).first()
                if customer:
                    customer.first_name = form.cleaned_data['first_name']
                    customer.last_name = form.cleaned_data['last_name']
                    customer.email = form.cleaned_data['email']
                    customer.notes = form.cleaned_data['notes']
                    customer.save()
                else:
                    customer = form.save(commit=False)
                    customer.business = business
                    customer.save()
                form = CustomerForm() # reset
    else:
        if editing_customer:
            form = CustomerForm(instance=editing_customer)
        else:
            form = CustomerForm()
        
    context = {
        'customers': customers,
        'form': form,
        'editing_customer': editing_customer,
    }
    return render(request, 'pages/crm/customers_list.jinja', context)


@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def delete_customer(request, customer_id):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)

    if request.method == 'POST':
        customer = get_object_or_404(Customer, id=customer_id, business=profile.business)
        customer.delete()
    return customers_list(request)
