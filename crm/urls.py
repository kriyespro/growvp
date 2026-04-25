from django.urls import path
from . import views

urlpatterns = [
    path('', views.customers_list, name='customers_list'),
    path('<int:customer_id>/delete/', views.delete_customer, name='delete_customer'),
]
