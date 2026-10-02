from django.contrib import admin

from django.contrib.auth.admin import UserAdmin

from .models import User, PhoneNumberVerification


class CustomUserAdmin(UserAdmin):
    search_fields = ("phone_number",)
    ordering = ("phone_number",)
    list_display = (
        "phone_number",
        "is_staff",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "phone_number_verified",
        "groups",
    )
    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "phone_number",
                    "password",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "phone_number_verified",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "fields": ("last_login",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


class PhoneNumberVerificationAdmin(admin.ModelAdmin):
    list_filter = ("is_active",)
    search_help_text = "Search by user phone number or request ID"
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    search_fields = (
        "user__phone_number",
        "request_id",
    )
    list_display = (
        'id',
        "user",
        'request_id',
        'created_at',
        'expires_at',
        'is_active',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(User, CustomUserAdmin)
admin.site.register(PhoneNumberVerification, PhoneNumberVerificationAdmin)
