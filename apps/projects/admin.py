from django.contrib import admin
from .models import Project

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'status', 'classification', 'created_at')
    list_filter = ('department', 'status', 'classification', 'created_at')
    search_fields = ('name', 'billing_destination')
    date_hierarchy = 'created_at'

admin.site.register(Project, ProjectAdmin)