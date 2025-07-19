from django.contrib import admin
from .models import Workload

@admin.register(Workload)
class WorkloadAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'department', 'year_month', 'total_hours', 'total_days')
    list_filter = ('department', 'year_month', 'created_at')
    search_fields = ('user__username', 'project__name')