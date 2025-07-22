from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date
from apps.users.models import Department, CustomUser

class CostMaster(models.Model):
    """コストマスター設定"""
    
    # 請求タイプ選択肢
    BILLING_TYPE_CHOICES = [
        ('monthly', '月額請求'),
        ('daily', '日額請求'),
        ('hourly', '時間請求'),
        ('fixed', '固定料金'),
    ]
    
    # 契約タイプ選択肢
    CONTRACT_TYPE_CHOICES = [
        ('regular', '通常契約'),
        ('volume_discount', 'ボリューム割引'),
        ('long_term', '長期契約'),
        ('special', '特別契約'),
        ('trial', '試用期間'),
    ]
    
    # 社員レベル選択肢（CustomUserから引用）
    EMPLOYEE_LEVEL_CHOICES = [
        ('junior', '新入社員'),
        ('middle', '中堅社員'),
        ('senior', 'シニア社員'),
        ('lead', 'リード社員'),
        ('manager', 'マネージャー'),
        ('director', 'ディレクター'),
    ]
    
    # 基本情報
    client_name = models.CharField('請求先', max_length=255)
    billing_type = models.CharField(
        '請求タイプ', 
        max_length=20, 
        choices=BILLING_TYPE_CHOICES
    )
    
    # 対象設定
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        verbose_name='対象部署',
        null=True, blank=True,
        help_text='設定しない場合は全部署が対象'
    )
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='責任者',
        help_text='案件の責任者を設定'
    )
    employee_level = models.CharField(
        '社員レベル', 
        max_length=20, 
        choices=EMPLOYEE_LEVEL_CHOICES,
        null=True, blank=True,
        help_text='対象となる社員レベルを設定'
    )
    
    # 請求単価設定
    monthly_billing = models.DecimalField(
        '月額請求単価（万円）', 
        max_digits=8, 
        decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    daily_billing = models.DecimalField(
        '日額請求単価（万円）', 
        max_digits=8, 
        decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    hourly_billing = models.DecimalField(
        '時間請求単価（円）', 
        max_digits=8, 
        decimal_places=0, 
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    fixed_billing = models.DecimalField(
        '固定請求料金（万円）', 
        max_digits=10, 
        decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # 割引・特別条件
    discount_rate = models.DecimalField(
        '割引率（%）', 
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    minimum_billing_amount = models.DecimalField(
        '最低請求金額（万円）', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    special_conditions = models.TextField(
        '特別条件',
        blank=True,
        help_text='割引条件や特別な取り決めなど'
    )
    
    # 契約条件
    contract_type = models.CharField(
        '契約タイプ', 
        max_length=20, 
        choices=CONTRACT_TYPE_CHOICES, 
        default='regular'
    )
    payment_terms = models.CharField(
        '支払い条件', 
        max_length=255, 
        blank=True,
        help_text='例：月末締め翌月末払い'
    )
    
    # 有効期間
    effective_from = models.DateField('有効開始日', default=date.today)
    effective_to = models.DateField('有効終了日', null=True, blank=True)
    
    # ステータス
    is_active = models.BooleanField('有効', default=True)
    
    # 管理情報
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cost_masters',
        verbose_name='作成者'
    )
    
    class Meta:
        verbose_name = 'コストマスター'
        verbose_name_plural = 'コストマスター'
        ordering = ['-created_at']
        unique_together = [
            ['client_name', 'department', 'employee_level', 'billing_type', 'effective_from']
        ]
    
    def __str__(self):
        parts = [self.client_name]
        if self.department:
            parts.append(f"({self.department.name})")
        if self.employee_level:
            parts.append(f"[{self.get_employee_level_display()}]")
        return " ".join(parts)
    
    def get_billing_amount(self):
        """請求タイプに応じた単価を取得"""
        if self.billing_type == 'monthly' and self.monthly_billing:
            return self.monthly_billing
        elif self.billing_type == 'daily' and self.daily_billing:
            return self.daily_billing
        elif self.billing_type == 'hourly' and self.hourly_billing:
            return self.hourly_billing
        elif self.billing_type == 'fixed' and self.fixed_billing:
            return self.fixed_billing
        return None
    
    def get_discounted_billing(self, base_amount=None):
        """割引適用後の請求金額を計算"""
        if base_amount is None:
            base_amount = self.get_billing_amount()
        
        if base_amount and self.discount_rate > 0:
            discounted = float(base_amount) * (1 - self.discount_rate / 100)
            return max(discounted, float(self.minimum_billing_amount))
        
        return float(base_amount) if base_amount else 0
    
    @property
    def is_expired(self):
        """有効期限切れかどうか"""
        if self.effective_to:
            return date.today() > self.effective_to
        return False
    
    @property
    def days_until_expiry(self):
        """有効期限までの日数"""
        if self.effective_to:
            delta = self.effective_to - date.today()
            return delta.days
        return None