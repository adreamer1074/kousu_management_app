from django.contrib import admin
from django.utils.html import format_html
from .models import CostMaster, ClientBillingRate, ProjectCostSetting

@admin.register(CostMaster)
class CostMasterAdmin(admin.ModelAdmin):
    list_display = [
        'department', 'employee_level', 'billing_type', 
        'monthly_billing', 'daily_billing', 'hourly_billing',
        'profit_margin_display', 'effective_from', 'is_active'
    ]
    list_filter = [
        'department', 'employee_level', 'billing_type', 
        'is_active', 'effective_from'
    ]
    search_fields = ['department__name']
    ordering = ['-effective_from']
    date_hierarchy = 'effective_from'
    
    fieldsets = (
        ('基本情報', {
            'fields': ('department', 'employee_level', 'billing_type')
        }),
        ('月額単価設定', {
            'fields': ('monthly_cost', 'monthly_billing'),
            'classes': ('collapse',)
        }),
        ('日額単価設定', {
            'fields': ('daily_cost', 'daily_billing'),
            'classes': ('collapse',)
        }),
        ('時間単価設定', {
            'fields': ('hourly_cost', 'hourly_billing'),
            'classes': ('collapse',)
        }),
        ('固定料金設定', {
            'fields': ('fixed_cost', 'fixed_billing'),
            'classes': ('collapse',)
        }),
        ('特別条件', {
            'fields': ('overtime_rate', 'holiday_rate'),
            'classes': ('collapse',)
        }),
        ('有効期間', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('department')
    
    def profit_margin_display(self, obj):
        margin = obj.profit_margin
        color = 'green' if margin > 20 else 'orange' if margin > 10 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, margin
        )
    profit_margin_display.short_description = '利益率'

@admin.register(ClientBillingRate)
class ClientBillingRateAdmin(admin.ModelAdmin):
    list_display = [
        'client_name', 'department', 'employee_level', 'billing_type',
        'monthly_billing', 'discount_rate', 'contract_type', 
        'effective_from', 'is_active'
    ]
    list_filter = [
        'department', 'employee_level', 'billing_type', 
        'contract_type', 'is_active'
    ]
    search_fields = ['client_name', 'department__name']
    ordering = ['client_name', '-effective_from']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('client_name', 'department', 'employee_level', 'billing_type')
        }),
        ('請求単価', {
            'fields': ('monthly_billing', 'daily_billing', 'hourly_billing', 'fixed_billing')
        }),
        ('割引・条件', {
            'fields': ('discount_rate', 'minimum_billing_amount', 'contract_type', 'payment_terms')
        }),
        ('有効期間', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
    )

@admin.register(ProjectCostSetting)
class ProjectCostSettingAdmin(admin.ModelAdmin):
    list_display = [
        'project_detail', 'use_client_specific_rate', 
        'billing_cycle', 'setup_cost', 'maintenance_cost'
    ]
    list_filter = [
        'use_client_specific_rate', 'billing_cycle', 
        'project_detail__status', 'project_detail__department'
    ]
    search_fields = [
        'project_detail__project_name', 
        'project_detail__case_name',
        'project_detail__billing_destination'
    ]
    
    fieldsets = (
        ('案件情報', {
            'fields': ('project_detail',)
        }),
        ('請求設定', {
            'fields': ('use_client_specific_rate', 'client_billing_rate')
        }),
        ('カスタム単価', {
            'fields': ('custom_monthly_billing', 'custom_daily_billing', 'custom_hourly_billing'),
            'classes': ('collapse',)
        }),
        ('追加費用', {
            'fields': ('setup_cost', 'maintenance_cost')
        }),
        ('請求条件', {
            'fields': ('billing_cycle', 'invoice_timing')
        }),
        ('備考', {
            'fields': ('cost_notes',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'project_detail__project', 
            'project_detail__department'
        )