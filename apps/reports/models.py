from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

User = get_user_model()

class WorkloadAggregation(models.Model):
    """工数集計一覧テーブル"""
    
    class StatusChoices(models.TextChoices):
        PLANNING = 'planning', '計画中'
        IN_PROGRESS = 'in_progress', '進行中'
        COMPLETED = 'completed', '完了'
        INSPECTION_WAITING = 'inspection_waiting', '検収待ち'
        INSPECTED = 'inspected', '検収済み'
        ON_HOLD = 'on_hold', '保留'
        CANCELLED = 'cancelled', 'キャンセル'
    
    class CaseClassificationChoices(models.TextChoices):
        DEVELOPMENT = 'development', '開発'
        MAINTENANCE = 'maintenance', '保守'
        SUPPORT = 'support', 'サポート'
        CONSULTING = 'consulting', 'コンサルティング'
        OTHER = 'other', 'その他'
    
    # 基本情報 - 既存のProjectTicketを使用
    project_name = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name='プロジェクト名',
        related_name='workload_aggregations_as_project'
    )
    case_name = models.ForeignKey(
        'projects.ProjectTicket',  # ProjectTicket
        on_delete=models.CASCADE,
        verbose_name='案件名（チケット）',
        related_name='workload_aggregations'
    )
    department = models.ForeignKey(
        'users.Department',
        on_delete=models.CASCADE,
        verbose_name='部名'
    )
    
    # 既存のフィールドはそのまま維持
    status = models.CharField(
        'ステータス',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNING
    )
    case_classification = models.CharField(
        '案件分類',
        max_length=20,
        choices=CaseClassificationChoices.choices,
        default=CaseClassificationChoices.DEVELOPMENT
    )
    
    # 日付関連
    estimate_date = models.DateField('見積日', null=True, blank=True)
    order_date = models.DateField('受注日', null=True, blank=True)
    planned_end_date = models.DateField('終了日（予定）', null=True, blank=True)
    actual_end_date = models.DateField('終了日実績（検収待ち）', null=True, blank=True)
    inspection_date = models.DateField('検収日', null=True, blank=True)
    
    # 金額関連（税別）
    available_amount = models.DecimalField(
        '使用可能金額（税別）',
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    billing_amount_excluding_tax = models.DecimalField(
        '請求金額（税別）',
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    outsourcing_cost_excluding_tax = models.DecimalField(
        '外注費（税別）',
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # 工数関連（人日）
    estimated_workdays = models.DecimalField(
        '見積工数（人日）',
        max_digits=8,
        decimal_places=1,
        default=Decimal('0.0'),
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    used_workdays = models.DecimalField(
        '使用工数（人日）',
        max_digits=8,
        decimal_places=1,
        default=Decimal('0.0'),
        validators=[MinValueValidator(Decimal('0.0'))],
        help_text='工数登録機能から自動計算'
    )
    newbie_workdays = models.DecimalField(
        '新入社員使用工数（人日）',
        max_digits=8,
        decimal_places=1,
        default=Decimal('0.0'),
        validators=[MinValueValidator(Decimal('0.0'))],
        help_text='ユーザーレベルがjuniorの工数を自動計算'
    )
    
    # 単価関連
    unit_cost_per_month = models.DecimalField(
        '単価（万円/月）',
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    billing_unit_cost_per_month = models.DecimalField(
        '請求単価（万円/月）',
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # 請求先情報
    billing_destination = models.CharField('請求先', max_length=200, blank=True)
    billing_contact = models.CharField('請求先担当者', max_length=100, blank=True)
    
    # 担当者
    mub_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='MUB担当者',
        related_name='managed_workload_aggregations'
    )
    
    # 備考
    remarks = models.TextField('備考', blank=True)
    
    # 管理情報
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_workload_aggregations',
        verbose_name='作成者'
    )
    
    class Meta:
        verbose_name = '工数集計'
        verbose_name_plural = '工数集計'
        ordering = ['-order_date', '-created_at']
    
    def __str__(self):
        return f"{self.project_name.name} - {self.case_name.title}"
    
    def calculate_workdays_from_workload(self):
        """工数登録機能から工数を自動計算（ProjectTicket対応版）"""
        from apps.workloads.models import WorkHour
        
        # ProjectTicketに関連する工数を取得
        work_hours = WorkHour.objects.filter(
            ticket=self.case_name,  # ProjectTicketを参照
            date__gte=self.order_date if self.order_date else None,
            date__lte=self.actual_end_date if self.actual_end_date else None
        )
        
        # 一般使用工数と新入社員工数を分離
        regular_workdays = Decimal('0.0')
        newbie_workdays = Decimal('0.0')
        
        for work_hour in work_hours:
            if hasattr(work_hour.user, 'employee_level') and work_hour.user.employee_level == 'junior':
                newbie_workdays += work_hour.hours
            else:
                regular_workdays += work_hour.hours
        
        # 時間を人日に変換（8時間=1人日として計算）
        self.used_workdays = regular_workdays / 8
        self.newbie_workdays = newbie_workdays / 8
        
        return {
            'used_workdays': self.used_workdays,
            'newbie_workdays': self.newbie_workdays,
            'total_workdays': self.used_workdays + self.newbie_workdays
        }
    
    # 既存のpropertyメソッドはそのまま維持
    @property
    def total_used_workdays(self):
        """使用工数合計（日）"""
        return self.used_workdays + self.newbie_workdays
    
    @property
    def remaining_workdays(self):
        """残工数（人日）"""
        return max(self.estimated_workdays - self.total_used_workdays, Decimal('0.0'))
    
    @property
    def remaining_amount(self):
        """残金額（税抜）"""
        return max(self.available_amount - self.billing_amount_excluding_tax, Decimal('0'))
    
    @property
    def profit_rate(self):
        """利益率"""
        if self.billing_amount_excluding_tax > 0:
            profit = self.billing_amount_excluding_tax - self.outsourcing_cost_excluding_tax
            return round((profit / self.billing_amount_excluding_tax) * 100, 1)
        return Decimal('0.0')
    
    @property
    def wip_amount(self):
        """仕掛中金額（人日×単価）"""
        return self.used_workdays * (self.unit_cost_per_month / 20)  # 月20日計算

# 既存のReportExportモデルはそのまま維持
class ReportExport(models.Model):
    """レポートエクスポート管理モデル"""
    name = models.CharField(
        max_length=200,
        verbose_name="レポート名"
    )
    report_type = models.CharField(
        max_length=20,
        choices=[
            ('monthly', '月次レポート'),
            ('project', 'プロジェクトレポート'),
            ('department', '部署レポート'),
        ],
        verbose_name="レポートタイプ"
    )
    format = models.CharField(
        max_length=10,
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
        ],
        default='pdf',
        verbose_name="フォーマット"
    )
    department = models.ForeignKey(
        'users.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="対象部署"
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="対象プロジェクト"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_reports',
        verbose_name="対象ユーザー"
    )
    start_date = models.DateField(
        verbose_name="開始日"
    )
    end_date = models.DateField(
        verbose_name="終了日"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="ファイルパス"
    )
    file_size = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="ファイルサイズ（バイト）"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '処理待ち'),
            ('processing', '処理中'),
            ('completed', '完了'),
            ('failed', '失敗'),
        ],
        default='pending',
        verbose_name="ステータス"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_reports',
        verbose_name="作成者"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="作成日時"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新日時"
    )

    class Meta:
        verbose_name = "レポートエクスポート"
        verbose_name_plural = "レポートエクスポート"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"