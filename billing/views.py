from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from decimal import Decimal
from booking.models import Appointment
from .models import Invoice

@login_required(login_url='/auth/login/')
@ensure_csrf_cookie
def checkout_modal(request, appointment_id):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)
    business = profile.business
    appointment = get_object_or_404(Appointment, id=appointment_id, business=business)
    
    subtotal = appointment.service.price
    tax = subtotal * Decimal('0.18')
    total = subtotal + tax
    
    # Ensure invoice exists
    invoice, created = Invoice.objects.get_or_create(
        appointment=appointment,
        defaults={
            'business': business,
            'subtotal': subtotal,
            'tax_amount': tax,
            'total_amount': total,
            'status': 'unpaid'
        }
    )
    
    # Keep invoice totals aligned with service pricing changes, but never
    # rewrite a paid invoice's amounts after the fact.
    if invoice.status != 'paid':
        fields_to_update = []
        if invoice.subtotal != subtotal:
            invoice.subtotal = subtotal
            fields_to_update.append('subtotal')
        if invoice.tax_amount != tax:
            invoice.tax_amount = tax
            fields_to_update.append('tax_amount')
        if invoice.total_amount != total:
            invoice.total_amount = total
            fields_to_update.append('total_amount')
        if fields_to_update:
            invoice.save(update_fields=fields_to_update)

    if request.method == 'POST' and request.POST.get('mark_paid') == '1':
        invoice.status = 'paid'
        invoice.save(update_fields=['status'])
        appointment.status = 'completed'
        appointment.save(update_fields=['status'])
        
        # Trigger an HTMX reload or return a success fragment
        from django.http import HttpResponse
        return HttpResponse('''
            <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/50 backdrop-blur-sm" id="checkout-modal">
                <div class="bg-creameSurface rounded-xl p-8 max-w-sm w-full shadow-lg text-center" @click.outside="document.getElementById('checkout-modal').remove()">
                    <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 mb-4">
                        <svg class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
                    </div>
                    <h3 class="text-xl font-bold text-textMain">Payment Logged</h3>
                    <p class="text-sm text-textMuted mt-2">The appointment is now complete and marked as paid.</p>
                    <button onclick="document.getElementById('checkout-modal').remove(); window.location.reload()" class="mt-6 w-full rounded-md bg-stone-100 px-3 py-2 text-sm font-semibold text-textMain shadow-sm ring-1 ring-inset ring-stone-300 hover:bg-stone-50">Close</button>
                </div>
            </div>
        ''')
        
    context = {
        'appointment': appointment,
        'invoice': invoice,
        'business': business
    }
    return render(request, 'pages/billing/checkout_modal.jinja', context)
