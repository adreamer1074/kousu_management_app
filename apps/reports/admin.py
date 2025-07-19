from django.contrib import admin
from .models import ReportExport

@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'report_type', 
        'format', 
        'status', 
        'created_at'  # exported_at → created_at に修正
    ]
    list_filter = [
        'report_type', 
        'format', 
        'status',
        'created_at'  # exported_at → created_at に修正
    ]
    search_fields = ['name', 'report_type']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'report_type', 'format', 'status')
        }),
        ('対象設定', {
            'fields': ('department', 'project', 'user', 'start_date', 'end_date')
        }),
        ('ファイル情報', {
            'fields': ('file_path', 'file_size')
        }),
        ('作成情報', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )