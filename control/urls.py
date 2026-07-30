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
    path("businesses/import/", views.businesses_import, name="businesses_import"),
    path(
        "businesses/import/sample/",
        views.businesses_import_sample,
        name="businesses_import_sample",
    ),
    path(
        "partner-listings/",
        views.partner_listings,
        name="partner_listings",
    ),
    path(
        "partner-listings/export/",
        views.partner_listings_export,
        name="partner_listings_export",
    ),
    path(
        "partner-listings/import/",
        views.partner_listings_import,
        name="partner_listings_import",
    ),
    path(
        "partner-listings/import/sample/",
        views.businesses_import_sample,
        name="partner_listings_import_sample",
    ),
    path(
        "partner-listings/bulk-delete/",
        views.partner_listings_bulk_delete,
        name="partner_listings_bulk_delete",
    ),
    path(
        "partner-listings/<int:pk>/edit/",
        views.partner_listing_edit,
        name="partner_listing_edit",
    ),
    path("partners/", views.partners_list, name="partners"),
    path("partners/assign/", views.partner_assign, name="partner_assign"),
    path("partners/unassign/", views.partner_unassign, name="partner_unassign"),
]
