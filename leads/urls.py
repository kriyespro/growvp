from django.urls import path

from leads import views

urlpatterns = [
    path("", views.inbox, name="leads_inbox"),
    path("<int:pk>/", views.thread, name="leads_thread"),
    path("new/<slug:business_slug>/", views.create_for_business, name="leads_create"),
]
