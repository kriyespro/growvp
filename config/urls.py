"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.urls import partner_urlpatterns, account_urlpatterns

urlpatterns = [
    path('admin/', include('control.urls', namespace='control')),
    path('sd/', admin.site.urls),  # Django admin backup panel
    path('auth/', include('users.urls')),
    path('partner/', include(partner_urlpatterns)),
    path('account/', include(account_urlpatterns)),
    path('leads/', include('leads.urls')),
    path('catalog/', include('catalog.urls')),
    path('crm/', include('crm.urls')),
    path('booking/', include('booking.urls')),
    path('billing/', include('billing.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
