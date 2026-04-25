from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_business, name='register_business'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('business-profile/', views.business_profile, name='business_profile'),
]
