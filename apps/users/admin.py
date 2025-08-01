from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_leader', 'is_active', 'date_joined')
    list_filter = ('is_leader', 'is_active', 'date_joined')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('department',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('department',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile)