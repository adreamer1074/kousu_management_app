from django.contrib import admin
from .models import Project, ProjectDetail

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """プロジェクト管理画面"""
    list_display = ['name', 'status', 'start_date', 'end_date', 'assigned_section', 'is_active']
    list_filter = ['status', 'assigned_section', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'client']
    filter_horizontal = ['assigned_users']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'description', 'client', 'status')
        }),
        ('期間・予算', {
            'fields': ('start_date', 'end_date', 'budget')
        }),
        ('担当者', {
            'fields': ('assigned_section', 'assigned_users')
        }),
        ('その他', {
            'fields': ('is_active',)
        }),
    )

@admin.register(ProjectDetail)
class ProjectDetailAdmin(admin.ModelAdmin):
    """プロジェクト詳細管理画面"""
    list_display = [
        'project_name', 'case_name', 'department', 'status', 
        'case_classification', 'budget_amount', 'billing_amount', 
        'estimated_workdays', 'used_workdays'
    ]
    list_filter = [
        'status', 'case_classification', 'department', 
        'estimate_date', 'order_date'
    ]
    search_fields = [
        'project_name', 'case_name', 'billing_destination', 
        'mub_manager', 'remarks'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('project', 'project_name', 'case_name', 'department', 'status', 'case_classification')
        }),
        ('日程情報', {
            'fields': ('estimate_date', 'order_date', 'planned_end_date', 'actual_end_date', 'inspection_date')
        }),
        ('金額情報（税別）', {
            'fields': ('budget_amount', 'billing_amount', 'outsourcing_cost')
        }),
        ('工数情報（人日）', {
            'fields': ('estimated_workdays', 'used_workdays', 'newbie_workdays')
        }),
        ('取引先情報', {
            'fields': ('billing_destination', 'billing_contact', 'mub_manager')
        }),
        ('その他', {
            'fields': ('remarks',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'department')
    
    # カスタム表示メソッド
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 編集時
            return ['project']  # プロジェクトは変更不可
        return []

    def save_model(self, request, obj, form, change):
        # プロジェクト名が変更された場合、関連するProjectも更新
        if obj.project:
            obj.project.name = obj.project_name
            obj.project.save()
        super().save_model(request, obj, form, change)