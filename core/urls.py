from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('b/<slug:business_slug>/', views.business_landing, name='business_landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/home', views.dashboard_home, name='dashboard_home'),
]
