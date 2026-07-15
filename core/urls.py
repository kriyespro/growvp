from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('pricing/', views.pricing, name='pricing'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('surat/', views.surat_hub, name='surat_hub'),
    path('surat/<slug:industry>/', views.surat_industry, name='surat_industry'),
    path(
        'surat/<slug:industry>/<slug:area_slug>/',
        views.surat_industry_area,
        name='surat_industry_area',
    ),
    path('directory/search/', views.directory_search, name='directory_search'),
    path('b/<slug:business_slug>/', views.business_landing, name='business_landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/home', views.dashboard_home, name='dashboard_home'),
]
