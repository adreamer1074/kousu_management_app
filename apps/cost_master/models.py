from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class CostMaster(models.Model):
    name = models.CharField(max_length=100, default='Unknown')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Cost Master'
        verbose_name_plural = 'Cost Masters'

class CostRate(models.Model):
    """コスト単価マスター"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cost_rates',
        verbose_name="ユーザー"
    )
    department = models.ForeignKey(
        'users.Department',  # 正しい参照
        on_delete=models.CASCADE,
        related_name='cost_rates',
        verbose_name="部署"
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=0,
        verbose_name="時間単価（円）"
    )
    effective_from = models.DateField(
        verbose_name="適用開始日"
    )
    effective_to = models.DateField(
        blank=True,
        null=True,
        verbose_name="適用終了日"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="アクティブ"
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
        verbose_name = "コスト単価"
        verbose_name_plural = "コスト単価"
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.user.username} - {self.hourly_rate}円/時間"