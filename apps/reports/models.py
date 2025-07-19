from django.db import models
from django.contrib.auth import get_user_model

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
        'users.Department',  # 修正: departments.Department → users.Department
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