from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Workload(models.Model):
    """工数管理モデル"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workloads',
        verbose_name="ユーザー"
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='workloads',
        verbose_name="プロジェクト"
    )
    department = models.ForeignKey(
        'users.Department',
        on_delete=models.CASCADE,
        related_name='workloads',
        verbose_name="部署"
    )
    section = models.ForeignKey(
        'users.Section',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workloads',
        verbose_name="課"
    )
    phase = models.ForeignKey(
        'projects.ProjectPhase',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workloads',
        verbose_name="フェーズ"
    )
    work_date = models.DateField(
        verbose_name="作業日"
    )
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="工数（時間）"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="作業内容"
    )
    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="残業時間"
    )
    year_month = models.CharField(
        max_length=7,
        verbose_name="年月",
        help_text="YYYY-MM形式"
    )
    is_billable = models.BooleanField(
        default=True,
        verbose_name="請求対象"
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
        verbose_name = "工数"
        verbose_name_plural = "工数"
        unique_together = ['user', 'project', 'work_date']
        ordering = ['-work_date']

    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.work_date}"

    def save(self, *args, **kwargs):
        # year_monthを自動設定
        if self.work_date:
            self.year_month = self.work_date.strftime('%Y-%m')
        super().save(*args, **kwargs)

    @property
    def total_hours(self):
        """総時間（通常時間＋残業時間）"""
        return self.hours + self.overtime_hours