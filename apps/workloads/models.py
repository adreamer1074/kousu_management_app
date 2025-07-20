from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Workload(models.Model):
    """工数モデル（カレンダー形式）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="担当者", related_name="workloads")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, verbose_name="プロジェクト", related_name="workloads")
    ticket = models.ForeignKey(
        "projects.ProjectTicket", 
        on_delete=models.CASCADE, 
        verbose_name="チケット", 
        related_name="workloads",
        null=True,
        blank=True
    )
    year_month = models.CharField(max_length=7, verbose_name="年月", help_text="YYYY-MM形式")
    
    # 各日の工数（時間）
    day_01 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="1日")
    day_02 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="2日")
    day_03 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="3日")
    day_04 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="4日")
    day_05 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="5日")
    day_06 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="6日")
    day_07 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="7日")
    day_08 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="8日")
    day_09 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="9日")
    day_10 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="10日")
    day_11 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="11日")
    day_12 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="12日")
    day_13 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="13日")
    day_14 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="14日")
    day_15 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="15日")
    day_16 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="16日")
    day_17 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="17日")
    day_18 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="18日")
    day_19 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="19日")
    day_20 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="20日")
    day_21 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="21日")
    day_22 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="22日")
    day_23 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="23日")
    day_24 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="24日")
    day_25 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="25日")
    day_26 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="26日")
    day_27 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="27日")
    day_28 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="28日")
    day_29 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="29日")
    day_30 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="30日")
    day_31 = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="31日")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        db_table = "workloads"
        verbose_name = "工数"
        verbose_name_plural = "工数"
        unique_together = ["user", "project", "ticket", "year_month"]
        indexes = [
            models.Index(fields=["year_month"]),
            models.Index(fields=["user", "year_month"]),
        ]
    
    def __str__(self):
        if self.ticket:
            return f"{self.user.username} - {self.ticket.title} - {self.year_month}"
        return f"{self.user.username} - {self.project.name} - {self.year_month}"
    
    def get_day_value(self, day):
        """指定された日の工数を取得"""
        try:
            day = int(day)
            field_name = f'day_{day:02d}'
            value = getattr(self, field_name, Decimal('0'))
            return float(value) if value is not None else 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def set_day_value(self, day, value):
        """指定された日の工数を設定"""
        try:
            day = int(day)
            field_name = f'day_{day:02d}'
            if hasattr(self, field_name):
                # Decimalに変換して設定
                decimal_value = Decimal(str(value)) if value else Decimal('0')
                setattr(self, field_name, decimal_value)
        except (ValueError, AttributeError, TypeError):
            pass
    
    @property
    def total_hours(self):
        """月の合計時間を計算"""
        total = Decimal('0')
        for day in range(1, 32):
            field_name = f'day_{day:02d}'
            if hasattr(self, field_name):
                value = getattr(self, field_name, Decimal('0'))
                if value is not None:
                    total += value
        return float(total)
    
    @property
    def total_days(self):
        """月の合計人日を計算（8時間 = 1人日）"""
        return self.total_hours / 8