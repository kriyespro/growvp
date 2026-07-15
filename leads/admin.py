from django.contrib import admin

from leads.models import Enquiry, EnquiryMessage


class EnquiryMessageInline(admin.TabularInline):
    model = EnquiryMessage
    extra = 0
    readonly_fields = ("sender", "body", "created_at")


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("id", "business", "client", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("subject", "business__name", "client__email")
    inlines = [EnquiryMessageInline]


@admin.register(EnquiryMessage)
class EnquiryMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "enquiry", "sender", "created_at")
    search_fields = ("body", "sender__email")
