from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:appointment_id>/', views.checkout_modal, name='checkout_modal'),
]
