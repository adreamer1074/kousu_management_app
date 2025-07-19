from django.contrib import admin
from .models import Workload

@admin.register(Workload)
class WorkloadAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'project', 
        'work_date',
        'hours',
        'overtime_hours',
        'total_hours_display'  # total_days → total_hours_display に修正
    ]
    list_filter = [
        'work_date',
        'department',
        'section',
        'project',
        'is_billable'
    ]
    search_fields = [
        'user__username',
        'project__name',
        'project__code',
        'description'
    ]
    readonly_fields = ['year_month', 'created_at', 'updated_at']
    ordering = ['-work_date']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'project', 'work_date', 'hours', 'overtime_hours')
        }),
        ('組織情報', {
            'fields': ('department', 'section', 'phase')
        }),
        ('詳細情報', {
            'fields': ('description', 'is_billable')
        }),
        ('自動設定', {
            'fields': ('year_month', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_hours_display(self, obj):
        """総時間を表示するメソッド"""
        return f"{obj.total_hours}時間"
    total_hours_display.short_description = "総時間"