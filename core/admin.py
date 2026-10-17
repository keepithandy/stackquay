from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AccessToken, Record, User

admin.site.site_header = "Stackquay administration"
admin.site.site_title = "Stackquay"
admin.site.index_title = "Manage users and records"


@admin.register(User)
class StackquayUserAdmin(UserAdmin):
    list_display = ["username", "email", "is_staff", "is_active", "date_joined"]
    add_fieldsets = UserAdmin.add_fieldsets + (("Contact", {"fields": ("email",)}),)


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "status", "updated_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "owner__username", "owner__email"]
    autocomplete_fields = ["owner"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "expires_at"]
    fields = ["user", "created_at", "expires_at"]
    readonly_fields = fields
    list_filter = ["expires_at"]
    search_fields = ["user__username"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
