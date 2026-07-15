from django.contrib import admin

from control.models import AdminLog


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "target_user", "message")
    list_filter = ("action", "created_at")
    search_fields = ("message", "actor__email", "target_user__email")
    readonly_fields = ("actor", "action", "target_user", "message", "ip_address", "created_at")
