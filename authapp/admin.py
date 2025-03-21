from django.contrib import admin
from .models import AppUser
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "address", "allergies")
    search_fields = ("user__username", "phone_number", "address", "allergies")
    list_filter = ("user__username", "phone_number", "address", "allergies")


class AppUserInline(admin.StackedInline):
    model = AppUser
    can_delete = False
    verbose_name_plural = "Profile"


class CustomUserAdmin(UserAdmin):
    inlines = (AppUserInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
