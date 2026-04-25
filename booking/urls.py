from django.urls import path
from . import views

urlpatterns = [
    path('calendar/', views.calendar_view, name='calendar'),
    path('b/<int:business_id>/', views.public_booking, name='public_booking'),
    path('<slug:business_slug>/', views.public_booking_by_slug, name='public_booking_by_slug'),
]
