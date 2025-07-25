from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
# CostMasterを削除して、新しいモデルのみインポート
from .models import BusinessPartner, OutsourcingCost, OutsourcingCostSummary


@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    """ビジネスパートナー管理画面"""
    
    list_display = [
        'name', 'company', 'hourly_rate_display', 'project_count', 
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'company']
    search_fields = ['name', 'company', 'email']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('契約情報', {
            'fields': ('hourly_rate', 'projects')
        }),
        ('ステータス', {
            'fields': ('is_active', 'notes')
        }),
        ('管理情報', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    filter_horizontal = ['projects']
    
    def hourly_rate_display(self, obj):
        """単価の表示"""
        return f"¥{obj.hourly_rate:,.0f}/時間"
    hourly_rate_display.short_description = '時間単価'
    
    def project_count(self, obj):
        """参加プロジェクト数"""
        count = obj.projects.count()
        if count > 0:
            return format_html(
                '<span style="color: green;">{} プロジェクト</span>',
                count
            )
        return format_html('<span style="color: gray;">0 プロジェクト</span>')
    project_count.short_description = '参加プロジェクト数'
    
    def save_model(self, request, obj, form, change):
        """保存時の処理"""
        if not change:  # 新規作成時
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OutsourcingCost)
class OutsourcingCostAdmin(admin.ModelAdmin):
    """外注費管理画面"""
    
    list_display = [
        'year_month', 'business_partner', 'project', 'ticket',
        'status_display', 'case_classification_display', 
        'work_hours', 'hourly_rate_display', 'total_cost_display'
    ]
    list_filter = [
        'year_month', 'status', 'case_classification', 
        'business_partner', 'project', 'created_at'
    ]
    search_fields = [
        'business_partner__name', 'project__name', 'ticket__title', 'notes'
    ]
    ordering = ['-year_month', 'business_partner__name']
    readonly_fields = [
        'hourly_rate', 'total_cost', 'created_at', 'updated_at', 'created_by'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('year_month', 'business_partner', 'project', 'ticket')
        }),
        ('作業情報', {
            'fields': ('status', 'case_classification', 'work_hours')
        }),
        ('金額情報', {
            'fields': ('hourly_rate', 'total_cost'),
            'description': '単価と外注費は自動計算されます'
        }),
        ('備考', {
            'fields': ('notes',)
        }),
        ('管理情報', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_display(self, obj):
        """ステータスの表示"""
        if obj.status == 'in_progress':
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> {}',
                obj.get_status_display()
            )
        else:
            return format_html(
                '<span style="color: gray;">○</span> {}',
                obj.get_status_display()
            )
    status_display.short_description = 'ステータス'
    
    def case_classification_display(self, obj):
        """案件分類の表示"""
        if obj.case_classification == 'development':
            return format_html(
                '<span style="background-color: #d1ecf1; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.get_case_classification_display()
            )
        else:
            return format_html(
                '<span style="background-color: #f8d7da; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.get_case_classification_display()
            )
    case_classification_display.short_description = '案件分類'
    
    def hourly_rate_display(self, obj):
        """単価の表示"""
        return f"¥{obj.hourly_rate:,.0f}"
    hourly_rate_display.short_description = '時間単価'
    
    def total_cost_display(self, obj):
        """外注費の表示"""
        if obj.status == 'in_progress':
            return format_html(
                '<strong style="color: green;">¥{:,.0f}</strong>',
                obj.total_cost
            )
        else:
            return format_html(
                '<span style="color: gray;">¥0</span>'
            )
    total_cost_display.short_description = '外注費'
    
    def save_model(self, request, obj, form, change):
        """保存時の処理"""
        if not change:  # 新規作成時
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['recalculate_costs']
    
    def recalculate_costs(self, request, queryset):
        """外注費の再計算"""
        updated_count = 0
        for obj in queryset:
            old_total = obj.total_cost
            obj.save()  # saveメソッドで自動計算される
            if obj.total_cost != old_total:
                updated_count += 1
        
        self.message_user(
            request,
            f'{updated_count}件の外注費を再計算しました。'
        )
    recalculate_costs.short_description = '選択した外注費を再計算'


@admin.register(OutsourcingCostSummary)
class OutsourcingCostSummaryAdmin(admin.ModelAdmin):
    """外注費月次集計管理画面"""
    
    list_display = [
        'year_month', 'total_records', 'in_progress_records', 
        'not_started_records', 'total_hours_display', 'total_cost_display',
        'last_calculated'
    ]
    list_filter = ['year_month', 'last_calculated']
    ordering = ['-year_month']
    readonly_fields = [
        'total_hours', 'total_cost', 'total_records',
        'in_progress_records', 'not_started_records', 'last_calculated'
    ]
    
    fieldsets = (
        ('集計期間', {
            'fields': ('year_month',)
        }),
        ('レコード数集計', {
            'fields': ('total_records', 'in_progress_records', 'not_started_records')
        }),
        ('金額集計', {
            'fields': ('total_hours', 'total_cost')
        }),
        ('更新情報', {
            'fields': ('last_calculated',)
        })
    )
    
    def total_hours_display(self, obj):
        """総作業時間の表示"""
        return f"{obj.total_hours:.1f}時間"
    total_hours_display.short_description = '総作業時間'
    
    def total_cost_display(self, obj):
        """総外注費の表示"""
        return format_html(
            '<strong style="color: green;">¥{:,.0f}</strong>',
            obj.total_cost
        )
    total_cost_display.short_description = '総外注費'
    
    actions = ['recalculate_summaries']
    
    def recalculate_summaries(self, request, queryset):
        """月次集計の再計算"""
        updated_count = 0
        for summary in queryset:
            OutsourcingCostSummary.calculate_summary(summary.year_month)
            updated_count += 1
        
        self.message_user(
            request,
            f'{updated_count}件の月次集計を再計算しました。'
        )
    recalculate_summaries.short_description = '選択した月次集計を再計算'
    
    def has_add_permission(self, request):
        """追加権限を無効化（自動生成のため）"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """削除権限を制限"""
        return request.user.is_superuser


# 管理画面のカスタマイズ
admin.site.site_header = '工数管理システム - 外注費管理'
admin.site.site_title = '外注費管理'
admin.site.index_title = '外注費管理システム'