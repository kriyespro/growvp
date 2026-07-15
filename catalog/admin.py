from django.contrib import admin
from .models import ServiceCategory, Service, BusinessHours, Product

admin.site.register(ServiceCategory)
admin.site.register(Service)
admin.site.register(BusinessHours)
admin.site.register(Product)
