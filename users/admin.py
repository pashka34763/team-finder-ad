from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class AdminUserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "name", "surname")


class AdminUserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = AdminUserEditForm
    add_form = AdminUserCreateForm

    list_display = ("email", "name", "surname", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff")
    search_fields = ("email", "name", "surname")
    ordering = ("-id",)
    filter_horizontal = ("favorites", "groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": ("name", "surname", "avatar", "phone", "github_url", "about")}),
        ("Избранное", {"fields": ("favorites",)}),
        (
            "Права",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "surname", "password1", "password2"),
            },
        ),
    )
