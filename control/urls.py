from django.urls import path

from control import views

app_name = "control"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("partials/stats/", views.stats_partial, name="stats_partial"),
    path("partials/activity/", views.activity_partial, name="activity_partial"),
    path("users/", views.users_list, name="users"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/ban/", views.user_ban, name="user_ban"),
    path("users/<int:pk>/unban/", views.user_unban, name="user_unban"),
    path("users/<int:pk>/impersonate/", views.impersonate, name="impersonate"),
    path("stop-impersonate/", views.stop_impersonate, name="stop_impersonate"),
    path("activity/", views.activity_page, name="activity"),
    path("businesses/", views.businesses_list, name="businesses"),
    path("partners/", views.partners_list, name="partners"),
    path("partners/assign/", views.partner_assign, name="partner_assign"),
    path("partners/unassign/", views.partner_unassign, name="partner_unassign"),
]
