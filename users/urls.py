from django.urls import path

from users import views

urlpatterns = [
    path("register/", views.register_business, name="register_business"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("business-profile/", views.business_profile, name="business_profile"),
    path("listing-plans/", views.listing_plans, name="listing_plans"),
]

partner_urlpatterns = [
    path("", views.partner_home, name="partner_home"),
    path("listings/", views.partner_listings, name="partner_listings"),
    path("listings/new/", views.partner_listing_create, name="partner_listing_create"),
    path(
        "listings/import/",
        views.partner_listing_import,
        name="partner_listing_import",
    ),
    path(
        "listings/import/sample/",
        views.partner_listing_import_sample,
        name="partner_listing_import_sample",
    ),
    path(
        "listings/<int:pk>/edit/",
        views.partner_listing_edit,
        name="partner_listing_edit",
    ),
]

account_urlpatterns = [
    path("", views.client_home, name="client_home"),
]
