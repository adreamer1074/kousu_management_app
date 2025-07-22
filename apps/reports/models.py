from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

User = get_user_model()

class ReportType(models.TextChoices):
    """レポートタイプ"""
    MONTHLY = 'monthly', '月次レポート'
    PROJECT = 'project', 'プロジェクトレポート'
    USER = 'user', 'ユーザーレポート'
    DEPARTMENT = 'department', '部署レポート'

class ReportFormat(models.TextChoices):
    """レポートフォーマット"""
    PDF = 'pdf', 'PDF'
    EXCEL = 'excel', 'Excel'
    CSV = 'csv', 'CSV'

class WorkloadAggregation(models.Model):
    """工数集計一覧テーブル（工数集計レポート機能）"""
    
    class StatusChoices(models.TextChoices):
        PLANNING = 'planning', '計画中'
        IN_PROGRESS = 'in_progress', '進行中'
        COMPLETED = 'completed', '完了'
        ON_HOLD = 'on_hold', '保留'
        CANCELLED = 'cancelled', 'キャンセル'
    
    # プロジェクト情報
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name='プロジェクト',
        related_name='workload_aggregations'
    )
    project_detail = models.ForeignKey(
        'projects.ProjectDetail',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='プロジェクト詳細'
    )
    
    # 期間設定
    year_month = models.CharField(
        '年月',
        max_length=7,  # YYYY-MM形式
        help_text='YYYY-MM形式（例：2024-12）'
    )
    
    # 予算・請求情報
    budget = models.DecimalField(
        '予算（万円）',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    billing_amount = models.DecimalField(
        '請求金額（万円）',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    outsourcing_cost = models.DecimalField(
        '外注費（万円）',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # 工数情報
    estimated_workdays = models.DecimalField(
        '見積工数（人日）',
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    used_workdays = models.DecimalField(
        '消化工数（人日）',
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # ステータス・進捗
    status = models.CharField(
        'ステータス',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNING
    )
    progress_rate = models.PositiveIntegerField(
        '進捗率（%）',
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # 部署・担当者情報
    department = models.ForeignKey(
        'users.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='担当部署'
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='プロジェクトマネージャー',
        related_name='managed_workload_aggregations'
    )
    
    # 備考・メモ
    notes = models.TextField('備考', blank=True)
    
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
        ordering = ['-year_month', '-created_at']
        unique_together = ['project', 'year_month']
    
    def __str__(self):
        return f"{self.project.name} - {self.year_month}"
    
    @property
    def workday_usage_rate(self):
        """工数消化率"""
        if self.estimated_workdays > 0:
            return round((self.used_workdays / self.estimated_workdays) * 100, 1)
        return 0
    
    @property
    def budget_usage_rate(self):
        """予算消化率"""
        if self.budget > 0:
            return round((self.billing_amount / self.budget) * 100, 1)
        return 0
    
    @property
    def remaining_workdays(self):
        """残り工数"""
        return max(self.estimated_workdays - self.used_workdays, 0)
    
    @property
    def remaining_budget(self):
        """残り予算"""
        return max(self.budget - self.billing_amount, 0)

class ReportExport(models.Model):
    """レポートエクスポート管理モデル"""
    name = models.CharField(
        max_length=200,
        verbose_name="レポート名"
    )
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        verbose_name="レポートタイプ"
    )
    format = models.CharField(
        max_length=10,
        choices=ReportFormat.choices,
        default=ReportFormat.PDF,
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