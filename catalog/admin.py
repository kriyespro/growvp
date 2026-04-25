from django.contrib import admin
from .models import ServiceCategory, Service, BusinessHours

admin.site.register(ServiceCategory)
admin.site.register(Service)
admin.site.register(BusinessHours)
