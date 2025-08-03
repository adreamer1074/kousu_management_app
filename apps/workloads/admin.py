from django.contrib import admin
from django.db.models import Sum, Count
from datetime import datetime
from .models import Workload

# 管理画面のカスタマイズ
admin.site.site_header = "工数管理システム"
admin.site.site_title = "工数管理システム"
admin.site.index_title = "システム管理"

# インデックスページの統計情報を追加
def get_admin_stats():
    """管理画面用の統計情報を取得"""
    from apps.users.models import CustomUser
    from apps.projects.models import Project, ProjectTicket
    from apps.workloads.models import WorkRecord
    from django.utils import timezone
    
    current_month = timezone.now().replace(day=1)
    
    return {
        'user_count': CustomUser.objects.filter(is_active=True).count(),
        'project_count': Project.objects.filter(is_active=True).count(),
        'ticket_count': ProjectTicket.objects.exclude(status='closed').count(),
        'workload_count': WorkRecord.objects.filter(
            work_date__gte=current_month
        ).count(),
    }

# カスタムAdminSiteを作成（オプション）
class CustomAdminSite(admin.AdminSite):
    site_header = "工数管理システム"
    site_title = "工数管理システム"
    index_title = "システム管理"
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(get_admin_stats())
        return super().index(request, extra_context)

# デフォルトのadmin.siteを使用する場合
def admin_index_context(request):
    """管理画面インデックスのコンテキストプロセッサー"""
    if request.path.startswith('/admin/'):
        return get_admin_stats()
    return {}

@admin.register(Workload)
class WorkloadAdmin(admin.ModelAdmin):
    """工数管理画面（カレンダー形式対応）"""
    list_display = [
        'user', 
        'project', 
        'ticket', 
        'year_month', 
        'get_department',
        'get_section',
        'total_hours', 
        'total_days',
        'created_at'
    ]
    list_filter = [
        'year_month',
        'user__department',  # userを通してdepartmentにアクセス
        'user__section',     # userを通してsectionにアクセス
        'project',
        'ticket__status',
        'created_at'
    ]
    search_fields = [
        'user__username',
        'user__first_name', 
        'user__last_name',
        'project__name',
        'ticket__title'
    ]
    readonly_fields = ['total_hours', 'total_days', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'project', 'ticket', 'year_month')
        }),
        ('工数情報', {
            'fields': (
                ('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07'),
                ('day_08', 'day_09', 'day_10', 'day_11', 'day_12', 'day_13', 'day_14'),
                ('day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20', 'day_21'),
                ('day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28'),
                ('day_29', 'day_30', 'day_31'),
            ),
            'classes': ('wide',)
        }),
        ('合計・メタ情報', {
            'fields': ('total_hours', 'total_days', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_department(self, obj):
        """部署名を取得"""
        if hasattr(obj.user, 'department') and obj.user.department:
            return obj.user.department.name
        return '-'
    get_department.short_description = '部署'
    get_department.admin_order_field = 'user__department__name'
    
    def get_section(self, obj):
        """課名を取得"""
        if hasattr(obj.user, 'section') and obj.user.section:
            return obj.user.section.name
        return '-'
    get_section.short_description = '課'
    get_section.admin_order_field = 'user__section__name'
    
    def total_hours(self, obj):
        """合計時間を表示"""
        return f"{obj.total_hours:.1f}時間"
    total_hours.short_description = '合計時間'
    
    def total_days(self, obj):
        """合計人日を表示"""
        return f"{obj.total_days:.1f}人日"
    total_days.short_description = '合計人日'
    
    def get_queryset(self, request):
        """クエリセットを最適化"""
        return super().get_queryset(request).select_related(
            'user',
            'user__department', 
            'user__section',
            'project',
            'ticket'
        )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """外部キーフィールドのクエリセットを最適化"""
        if db_field.name == "user":
            kwargs["queryset"] = db_field.related_model.objects.select_related(
                'department', 'section'
            ).order_by('username')
        elif db_field.name == "project":
            kwargs["queryset"] = db_field.related_model.objects.filter(
                is_active=True
            ).order_by('name')
        elif db_field.name == "ticket":
            kwargs["queryset"] = db_field.related_model.objects.select_related(
                'project'
            ).order_by('project__name', 'title')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    # カスタムアクション
    actions = ['export_workload_summary']
    
    def export_workload_summary(self, request, queryset):
        """選択された工数のサマリーを表示"""
        total_hours = sum(w.total_hours for w in queryset)
        total_days = total_hours / 8
        
        self.message_user(
            request, 
            f"選択された{queryset.count()}件の工数合計: "
            f"{total_hours:.1f}時間 ({total_days:.1f}人日)"
        )
    export_workload_summary.short_description = "選択された工数のサマリーを表示"
    
    # 日付フィールドの階層表示
    date_hierarchy = 'created_at'
    
    # ページあたりの表示件数
    list_per_page = 50
    list_max_show_all = 200
    
    class Media:
        css = {
            'all': ('admin/css/workload_admin.css',)
        }
        js = ('admin/js/workload_admin.js',)