from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.users.models import Department

class CostMaster(models.Model):
    """単価・費用マスター"""
    
    EMPLOYEE_LEVEL_CHOICES = [
        ('junior', '新入社員'),
        ('mid', '中堅社員'),
        ('senior', '上級社員'),
        ('manager', '管理職'),
        ('expert', 'エキスパート'),
    ]
    
    BILLING_TYPE_CHOICES = [
        ('monthly', '月額単価'),
        ('daily', '日額単価'),
        ('hourly', '時間単価'),
        ('fixed', '固定料金'),
    ]
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='部署', null=True, blank=True, default=None)
    employee_level = models.CharField('社員レベル', max_length=50, choices=EMPLOYEE_LEVEL_CHOICES, null=True, blank=True, default='mid')
    billing_type = models.CharField('請求タイプ', max_length=20, choices=BILLING_TYPE_CHOICES, null=True, blank=True, default=None)

    # 単価情報（万円/月）
    monthly_cost = models.DecimalField('原価（万円/月）', max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    monthly_billing = models.DecimalField('請求単価（万円/月）', max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # 日額単価（万円/日）
    daily_cost = models.DecimalField('日額原価（万円/日）', max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    daily_billing = models.DecimalField('日額請求単価（万円/日）', max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # 時間単価（円/時間）
    hourly_cost = models.DecimalField('時間単価原価（円/時間）', max_digits=8, decimal_places=0, default=0, validators=[MinValueValidator(0)])
    hourly_billing = models.DecimalField('時間単価請求（円/時間）', max_digits=8, decimal_places=0, default=0, validators=[MinValueValidator(0)])
    
    # 固定料金（万円）
    fixed_cost = models.DecimalField('固定原価（万円）', max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    fixed_billing = models.DecimalField('固定請求料金（万円）', max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # 有効期間
    effective_from = models.DateField('有効開始日', default=timezone.now)
    effective_to = models.DateField('有効終了日', null=True, blank=True)
    
    # 追加設定
    overtime_rate = models.DecimalField('残業単価倍率', max_digits=3, decimal_places=2, default=Decimal('1.25'), validators=[MinValueValidator(1.0)])
    holiday_rate = models.DecimalField('休日単価倍率', max_digits=3, decimal_places=2, default=Decimal('1.35'), validators=[MinValueValidator(1.0)])
    
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        verbose_name = 'コストマスター'
        verbose_name_plural = 'コストマスター'
        ordering = ['-effective_from']
        unique_together = ['department', 'employee_level', 'billing_type', 'effective_from']
    
    def __str__(self):
        return f"{self.department.name} - {self.get_employee_level_display()} - {self.get_billing_type_display()} ({self.effective_from})"
    
    @property
    def calculated_daily_cost(self):
        """計算された日次原価"""
        if self.billing_type == 'daily':
            return self.daily_cost
        elif self.billing_type == 'monthly':
            return self.monthly_cost / 20  # 月20日換算
        elif self.billing_type == 'hourly':
            return self.hourly_cost * 8 / 10000  # 8時間/日、万円換算
        return 0
    
    @property
    def calculated_daily_billing(self):
        """計算された日次請求単価"""
        if self.billing_type == 'daily':
            return self.daily_billing
        elif self.billing_type == 'monthly':
            return self.monthly_billing / 20  # 月20日換算
        elif self.billing_type == 'hourly':
            return self.hourly_billing * 8 / 10000  # 8時間/日、万円換算
        return 0
    
    @property
    def profit_margin(self):
        """利益率（%）"""
        if self.billing_type == 'monthly' and self.monthly_billing > 0:
            return ((self.monthly_billing - self.monthly_cost) / self.monthly_billing) * 100
        elif self.billing_type == 'daily' and self.daily_billing > 0:
            return ((self.daily_billing - self.daily_cost) / self.daily_billing) * 100
        elif self.billing_type == 'hourly' and self.hourly_billing > 0:
            return ((self.hourly_billing - self.hourly_cost) / self.hourly_billing) * 100
        elif self.billing_type == 'fixed' and self.fixed_billing > 0:
            return ((self.fixed_billing - self.fixed_cost) / self.fixed_billing) * 100
        return 0
    
    def get_cost_for_workdays(self, workdays, is_overtime=False, is_holiday=False):
        """工数に基づくコスト計算"""
        base_cost = self.calculated_daily_cost * workdays
        
        if is_overtime:
            base_cost *= self.overtime_rate
        if is_holiday:
            base_cost *= self.holiday_rate
            
        return base_cost
    
    def get_billing_for_workdays(self, workdays, is_overtime=False, is_holiday=False):
        """工数に基づく請求金額計算"""
        base_billing = self.calculated_daily_billing * workdays
        
        if is_overtime:
            base_billing *= self.overtime_rate
        if is_holiday:
            base_billing *= self.holiday_rate
            
        return base_billing

class ClientBillingRate(models.Model):
    """取引先別請求単価設定"""
    
    client_name = models.CharField('取引先名', max_length=200)
    
    # departmentをオプションに変更
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        verbose_name='部署',
        null=True, blank=True,  # 追加
        help_text='設定しない場合は全部署が対象'
    )
    
    # employee_levelもオプションに変更
    employee_level = models.CharField(
        '社員レベル', 
        max_length=50, 
        choices=CostMaster.EMPLOYEE_LEVEL_CHOICES,
        null=True, blank=True,  # 追加
        help_text='設定しない場合は全レベルが対象'
    )
    
    # billing_typeもオプションに変更
    billing_type = models.CharField(
        '請求タイプ', 
        max_length=20, 
        choices=CostMaster.BILLING_TYPE_CHOICES, 
        null=True, blank=True  # 追加（defaultを削除）
    )
    
    # 取引先別単価（すべてオプション）
    monthly_billing = models.DecimalField(
        '月額請求単価（万円）', 
        max_digits=8, 
        decimal_places=2, 
        null=True, blank=True,  # 変更
        validators=[MinValueValidator(0)]
    )
    daily_billing = models.DecimalField(
        '日額請求単価（万円）', 
        max_digits=8, 
        decimal_places=2, 
        null=True, blank=True,  # 変更
        validators=[MinValueValidator(0)]
    )
    hourly_billing = models.DecimalField(
        '時間請求単価（円）', 
        max_digits=8, 
        decimal_places=0, 
        null=True, blank=True,  # 変更
        validators=[MinValueValidator(0)]
    )
    fixed_billing = models.DecimalField(
        '固定請求料金（万円）', 
        max_digits=10, 
        decimal_places=2, 
        null=True, blank=True,  # 変更
        validators=[MinValueValidator(0)]
    )
    
    # 割引・特別条件
    discount_rate = models.DecimalField('割引率（%）', max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    minimum_billing_amount = models.DecimalField('最低請求金額（万円）', max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # 有効期間
    effective_from = models.DateField('有効開始日', default=timezone.now)
    effective_to = models.DateField('有効終了日', null=True, blank=True)
    
    # 契約条件
    contract_type = models.CharField('契約タイプ', max_length=50, choices=[
        ('regular', '通常契約'),
        ('volume_discount', 'ボリューム割引'),
        ('long_term', '長期契約'),
        ('special', '特別契約'),
    ], default='regular')
    
    payment_terms = models.CharField('支払い条件', max_length=100, blank=True, help_text='例：月末締め翌月末払い')
    
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        verbose_name = '取引先別請求単価'
        verbose_name_plural = '取引先別請求単価'
        ordering = ['client_name', '-effective_from']
        # unique_togetherを調整（null値を考慮）
    
    def __str__(self):
        parts = [self.client_name]
        if self.department:
            parts.append(f"({self.department.name})")
        if self.employee_level:
            parts.append(f"[{self.get_employee_level_display()}]")
        return " ".join(parts)
    
    def get_discounted_billing(self, base_amount):
        """割引適用後請求金額"""
        if self.discount_rate > 0:
            discounted = base_amount * (1 - self.discount_rate / 100)
            return max(discounted, self.minimum_billing_amount)
        return max(base_amount, self.minimum_billing_amount)

class ProjectCostSetting(models.Model):
    """案件別コスト設定"""
    
    project_detail = models.OneToOneField(
        'projects.ProjectDetail', 
        on_delete=models.CASCADE, 
        related_name='cost_setting',
        verbose_name='案件詳細'
    )
    
    # 基本設定
    use_client_specific_rate = models.BooleanField('取引先別単価を使用', default=False)
    client_billing_rate = models.ForeignKey(
        ClientBillingRate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='取引先別単価'
    )
    
    # カスタム単価設定
    custom_monthly_billing = models.DecimalField('カスタム月額単価（万円）', max_digits=8, decimal_places=2, null=True, blank=True)
    custom_daily_billing = models.DecimalField('カスタム日額単価（万円）', max_digits=8, decimal_places=2, null=True, blank=True)
    custom_hourly_billing = models.DecimalField('カスタム時間単価（円）', max_digits=8, decimal_places=0, null=True, blank=True)
    
    # 追加費用
    setup_cost = models.DecimalField('初期費用（万円）', max_digits=10, decimal_places=2, default=0)
    maintenance_cost = models.DecimalField('保守費用（万円/月）', max_digits=8, decimal_places=2, default=0)
    
    # 請求条件
    billing_cycle = models.CharField('請求サイクル', max_length=20, choices=[
        ('monthly', '月次'),
        ('milestone', 'マイルストーン'),
        ('completion', '完了時'),
        ('custom', 'カスタム'),
    ], default='monthly')
    
    invoice_timing = models.CharField('請求タイミング', max_length=50, blank=True, help_text='例：毎月末、検収後30日以内')
    
    # 備考
    cost_notes = models.TextField('コスト備考', blank=True)
    
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        verbose_name = '案件別コスト設定'
        verbose_name_plural = '案件別コスト設定'
    
    def __str__(self):
        return f"{self.project_detail.project_name} - コスト設定"
    
    def get_applicable_billing_rate(self, employee_level='mid'):
        """適用する請求単価を取得"""
        if self.use_client_specific_rate and self.client_billing_rate:
            return self.client_billing_rate
        
        # デフォルトの部署別単価を取得
        return CostMaster.objects.filter(
            department=self.project_detail.department,
            employee_level=employee_level,
            is_active=True,
            effective_from__lte=timezone.now().date()
        ).first()
    
    def calculate_total_project_cost(self):
        """プロジェクト総コスト計算"""
        base_cost = self.project_detail.get_total_cost()
        additional_cost = self.setup_cost + (self.maintenance_cost * 12)  # 年間保守費用
        return base_cost + additional_cost