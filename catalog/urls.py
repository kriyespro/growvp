from django.urls import path
from . import views

urlpatterns = [
    path('services/', views.services_list, name='services_list'),
    path('services/<int:service_id>/delete/', views.delete_service, name='delete_service'),
    path('categories/', views.categories_list, name='categories_list'),
]
