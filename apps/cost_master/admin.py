from django.contrib import admin
from .models import CostMaster

@admin.register(CostMaster)
class CostMasterAdmin(admin.ModelAdmin):
    """コストマスター管理画面"""
    
    list_display = [
        'client_name', 'billing_type', 'department', 'employee_level',
        'get_billing_amount', 'discount_rate', 'contract_type', 
        'effective_from', 'effective_to', 'is_active', 'created_at'
    ]
    
    list_filter = [
        'billing_type', 'contract_type', 'department', 'employee_level', 
        'is_active', 'created_at'
    ]
    
    search_fields = [
        'client_name', 'payment_terms', 'special_conditions'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('client_name', 'billing_type')
        }),
        ('対象設定', {
            'fields': ('department', 'manager', 'employee_level'),
            'classes': ('collapse',)
        }),
        ('請求単価設定', {
            'fields': (
                'monthly_billing', 'daily_billing', 
                'hourly_billing', 'fixed_billing'
            )
        }),
        ('割引・特別条件', {
            'fields': (
                'discount_rate', 'minimum_billing_amount', 'special_conditions'
            ),
            'classes': ('collapse',)
        }),
        ('契約条件', {
            'fields': ('contract_type', 'payment_terms'),
            'classes': ('collapse',)
        }),
        ('有効期間', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
        ('管理情報', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_billing_amount(self, obj):
        """請求金額の表示"""
        amount = obj.get_billing_amount()
        if amount:
            if obj.billing_type == 'hourly':
                return f"{amount:,.0f}円"
            else:
                return f"{amount:,.1f}万円"
        return "-"
    get_billing_amount.short_description = '請求金額'
    
    def save_model(self, request, obj, form, change):
        """保存時に作成者を設定"""
        if not change:  # 新規作成時
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related(
            'department', 'manager', 'created_by'
        )
    
    # カスタムアクション
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        """選択したレコードを有効にする"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated}件のレコードを有効にしました。')
    make_active.short_description = '選択したコストマスターを有効にする'
    
    def make_inactive(self, request, queryset):
        """選択したレコードを無効にする"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated}件のレコードを無効にしました。')
    make_inactive.short_description = '選択したコストマスターを無効にする'