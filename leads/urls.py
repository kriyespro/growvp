from django.urls import path

from leads import views

urlpatterns = [
    path("", views.inbox, name="leads_inbox"),
    path("bulk-status/", views.enquiry_bulk_status, name="leads_bulk_status"),
    path("<int:pk>/", views.thread, name="leads_thread"),
    path("<int:pk>/status/", views.enquiry_set_status, name="leads_set_status"),
    path("new/<slug:business_slug>/", views.create_for_business, name="leads_create"),
]
