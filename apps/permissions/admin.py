from django.contrib import admin
from .models import Permission

class PermissionAdmin(admin.ModelAdmin):
    list_display = ('group', 'department', 'can_view', 'can_edit', 'can_export')
    list_filter = ('group', 'department')
    search_fields = ('group__name', 'department__name')

admin.site.register(Permission, PermissionAdmin)