from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

UserAdmin.fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
UserAdmin.list_display = UserAdmin.list_display + ("role",)

admin.site.register(User, UserAdmin)
