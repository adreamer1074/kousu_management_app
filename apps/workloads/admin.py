from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from .models import Workload

@admin.register(Workload)
class WorkloadAdmin(admin.ModelAdmin):
    """工数管理画面（カレンダー形式対応）"""
    list_display = [
        'year_month', 'user_display', 'project_display', 'department_display',
        'total_hours_display', 'total_days_display', 'created_at_display'
    ]
    list_filter = [
        'year_month', 'department', 'project', 'user', 'created_at',
        ('created_at', admin.DateFieldListFilter),
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 
        'project__name', 'department__name', 'year_month'
    ]
    ordering = ['-year_month', 'department__name', 'user__username', 'project__name']
    readonly_fields = ['total_hours', 'total_days', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'project', 'department', 'year_month')
        }),
        ('工数合計', {
            'fields': ('total_hours', 'total_days'),
            'classes': ('collapse',)
        }),
        ('日別工数', {
            'fields': (
                ('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07'),
                ('day_08', 'day_09', 'day_10', 'day_11', 'day_12', 'day_13', 'day_14'),
                ('day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20', 'day_21'),
                ('day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28'),
                ('day_29', 'day_30', 'day_31'),
            ),
            'classes': ('wide',)
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # 年月順でグループ化
    date_hierarchy = 'created_at'  # year_monthフィールドは文字列なのでcreated_atを使用
    
    # ページネーション
    list_per_page = 50
    
    def get_queryset(self, request):
        """関連オブジェクトを事前取得してパフォーマンス向上"""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'project', 'department')
    
    def user_display(self, obj):
        """ユーザー表示をカスタマイズ"""
        full_name = obj.user.get_full_name()
        if full_name:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                full_name,
                obj.user.username
            )
        return obj.user.username
    user_display.short_description = 'ユーザー'
    
    def project_display(self, obj):
        """プロジェクト表示をカスタマイズ"""
        return format_html(
            '<span style="color: #0066cc;">{}</span>',
            obj.project.name
        )
    project_display.short_description = 'プロジェクト'
    
    def department_display(self, obj):
        """部署表示をカスタマイズ"""
        if obj.department:
            return format_html(
                '<span style="color: #28a745;">{}</span>',
                obj.department.name
            )
        return '-'
    department_display.short_description = '部署'
    
    def total_hours_display(self, obj):
        """工数表示をカスタマイズ"""
        return format_html(
            '<strong>{}</strong> 時間',
            obj.total_hours
        )
    total_hours_display.short_description = '合計時間'
    
    def total_days_display(self, obj):
        """人日表示をカスタマイズ"""
        return format_html(
            '<strong>{}</strong> 人日',
            obj.total_days
        )
    total_days_display.short_description = '合計人日'
    
    def created_at_display(self, obj):
        """作成日時表示をカスタマイズ"""
        return obj.created_at.strftime('%Y/%m/%d %H:%M')
    created_at_display.short_description = '登録日時'
    
    def save_model(self, request, obj, form, change):
        """保存時に部署を自動設定"""
        if not obj.department:
            if obj.user.department:
                obj.department = obj.user.department
            elif obj.user.section and obj.user.section.department:
                obj.department = obj.user.section.department
        super().save_model(request, obj, form, change)
    
    def changelist_view(self, request, extra_context=None):
        """管理画面に統計情報を追加"""
        extra_context = extra_context or {}
        
        # 現在表示されている工数の統計
        changelist = self.get_changelist_instance(request)
        filtered_queryset = changelist.get_queryset(request)
        
        stats = filtered_queryset.aggregate(
            total_hours=Sum('total_hours'),
            total_days=Sum('total_days')
        )
        
        extra_context.update({
            'total_hours': stats['total_hours'] or 0,
            'total_days': stats['total_days'] or 0,
            'total_workloads': filtered_queryset.count(),
            'unique_users': filtered_queryset.values('user').distinct().count(),
            'unique_projects': filtered_queryset.values('project').distinct().count(),
            'unique_departments': filtered_queryset.values('department').distinct().count(),
        })
        
        return super().changelist_view(request, extra_context)

# 管理画面のタイトルをカスタマイズ
admin.site.site_header = "工数管理システム 管理画面"
admin.site.site_title = "工数管理"
admin.site.index_title = "システム管理"