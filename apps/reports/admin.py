from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

try:
    from .models import ReportExport, WorkloadAggregation
except ImportError as e:
    # モデルが見つからない場合のフォールバック
    ReportExport = None
    WorkloadAggregation = None
    print(f"Warning: Could not import models: {e}")

@admin.register(WorkloadAggregation)
class WorkloadAggregationAdmin(admin.ModelAdmin):
    """工数集計管理"""
    list_display = [
        'project_name', 'case_name', 'department', 'status', 'case_classification',
        'order_date', 'actual_end_date', 'available_amount', 'billing_amount_excluding_tax',
        'used_workdays', 'newbie_workdays', 'total_used_workdays_display',
        'remaining_amount_display', 'profit_rate_display', 'created_at'
    ]
    list_filter = [
        'status', 'case_classification', 'department', 'order_date', 'actual_end_date',
        'created_at', 'updated_at'
    ]
    search_fields = [
        'project_name__name', 'case_name__title', 'billing_destination',
        'billing_contact', 'remarks'
    ]
    readonly_fields = [
        'used_workdays', 'newbie_workdays', 'total_used_workdays_display',
        'remaining_workdays_display', 'remaining_amount_display', 'profit_rate_display',
        'wip_amount_display', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('project_name', 'case_name', 'department', 'status', 'case_classification')
        }),
        ('日付情報', {
            'fields': ('estimate_date', 'order_date', 'planned_end_date', 'actual_end_date', 'inspection_date')
        }),
        ('金額情報（税別）', {
            'fields': ('available_amount', 'billing_amount_excluding_tax', 'outsourcing_cost_excluding_tax',
                      'remaining_amount_display', 'profit_rate_display')
        }),
        ('工数情報', {
            'fields': ('estimated_workdays', 'used_workdays', 'newbie_workdays',
                      'total_used_workdays_display', 'remaining_workdays_display', 'wip_amount_display')
        }),
        ('単価情報', {
            'fields': ('unit_cost_per_month', 'billing_unit_cost_per_month')
        }),
        ('請求先情報', {
            'fields': ('billing_destination', 'billing_contact', 'mub_manager')
        }),
        ('その他', {
            'fields': ('remarks',)
        }),
        ('管理情報', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def total_used_workdays_display(self, obj):
        """使用工数合計表示"""
        return f"{obj.total_used_workdays:.1f}人日"
    total_used_workdays_display.short_description = "使用工数合計"
    
    def remaining_workdays_display(self, obj):
        """残工数表示"""
        return f"{obj.remaining_workdays:.1f}人日"
    remaining_workdays_display.short_description = "残工数"
    
    def remaining_amount_display(self, obj):
        """残金額表示"""
        return f"¥{obj.remaining_amount:,}"
    remaining_amount_display.short_description = "残金額"
    
    def profit_rate_display(self, obj):
        """利益率表示"""
        rate = obj.profit_rate
        color = 'green' if rate >= 20 else 'orange' if rate >= 10 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    profit_rate_display.short_description = "利益率"
    
    def wip_amount_display(self, obj):
        """仕掛中金額表示"""
        return f"¥{(obj.wip_amount * 10000):,.0f}"
    wip_amount_display.short_description = "仕掛中金額"
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新規作成時
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

if ReportExport:
    @admin.register(ReportExport)
    class ReportExportAdmin(admin.ModelAdmin):
        """レポートエクスポート管理"""
        list_display = [
            'file_name', 'export_type', 'export_format', 'status',
            'file_size_display', 'requested_by', 'requested_at',
            'processing_time_display', 'download_count', 'is_expired_display'
        ]
        list_filter = [
            'export_type', 'export_format', 'status', 'is_public',
            'requested_at', 'completed_at'
        ]
        search_fields = ['file_name', 'description', 'requested_by__username']
        readonly_fields = [
            'file_size', 'total_records', 'exported_records',
            'processing_time_display', 'download_count', 'requested_at',
            'started_at', 'completed_at'
        ]
        
        fieldsets = (
            ('基本情報', {
                'fields': ('export_type', 'export_format', 'file_name', 'description')
            }),
            ('ファイル情報', {
                'fields': ('file_path', 'file_size', 'is_public')
            }),
            ('処理状況', {
                'fields': ('status', 'total_records', 'exported_records', 'error_message')
            }),
            ('日時情報', {
                'fields': ('requested_at', 'started_at', 'completed_at', 'expires_at')
            }),
            ('利用状況', {
                'fields': ('download_count', 'processing_time_display')
            }),
            ('フィルター条件', {
                'fields': ('filter_conditions',),
                'classes': ('collapse',)
            })
        )
        
        def file_size_display(self, obj):
            """ファイルサイズ表示"""
            return obj.get_file_size_display()
        file_size_display.short_description = "ファイルサイズ"
        
        def processing_time_display(self, obj):
            """処理時間表示"""
            time = obj.processing_time
            if time is not None:
                return f"{time:.2f}秒"
            return "-"
        processing_time_display.short_description = "処理時間"
        
        def is_expired_display(self, obj):
            """有効期限表示"""
            if obj.is_expired:
                return format_html('<span style="color: red;">期限切れ</span>')
            elif obj.expires_at:
                return format_html('<span style="color: green;">有効</span>')
            return "-"
        is_expired_display.short_description = "有効期限"
        
        def save_model(self, request, obj, form, change):
            if not change:  # 新規作成時
                obj.requested_by = request.user
            super().save_model(request, obj, form, change)