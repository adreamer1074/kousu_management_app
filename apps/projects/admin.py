from django.contrib import admin
from .models import Project, ProjectTicket

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """プロジェクト管理画面"""
    list_display = [
        'name', 'client', 'status', 
        'start_date', 'end_date', 'assigned_section', 'is_active', 'created_at'
    ]
    list_filter = ['status', 'is_active', 'created_at', 'start_date', 'assigned_section']
    search_fields = ['name', 'client', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'description')
        }),
        ('プロジェクト詳細', {
            'fields': ('client', 'status', 'start_date', 'end_date', 'budget')
        }),
        ('担当', {
            'fields': ('assigned_section', 'assigned_users')
        }),
        ('設定', {
            'fields': ('is_active',)
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['assigned_users']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_section').prefetch_related('assigned_users')

@admin.register(ProjectTicket)
class ProjectTicketAdmin(admin.ModelAdmin):
    """プロジェクトチケット管理画面"""
    list_display = [
        'title', 'project', 'priority', 'status', 
        'assigned_user', 'due_date', 'created_at'
    ]
    list_filter = ['priority', 'status', 'created_at', 'due_date']
    search_fields = ['title', 'project__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('project', 'title', 'description')
        }),
        ('設定', {
            'fields': ('priority', 'status', 'assigned_user', 'due_date')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'assigned_user')