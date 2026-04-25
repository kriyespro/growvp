from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Business, UserProfile

admin.site.register(User, UserAdmin)

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'industry_type', 'created_at')
    search_fields = ('name', 'slug')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business', 'role')
