from django.db import models
from django.contrib.auth import get_user_model
from apps.projects.models import Project
from apps.users.models import Department
import calendar

User = get_user_model()

class Workload(models.Model):
    """工数モデル（カレンダー形式）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="担当者", related_name="workloads")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="案件", related_name="workloads")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="部署", related_name="workloads", null=True, blank=True)
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
    
    total_hours = models.DecimalField(max_digits=6, decimal_places=1, default=0, verbose_name="月間合計時間")
    total_days = models.DecimalField(max_digits=5, decimal_places=1, default=0, verbose_name="月間合計人日")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "工数"
        verbose_name_plural = "工数"
        ordering = ['-year_month', 'department', 'user', 'project']
        unique_together = ['user', 'project', 'year_month']

    def save(self, *args, **kwargs):
        if not self.department and self.user.department:
            self.department = self.user.department
        self.calculate_totals()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        total = sum(getattr(self, f'day_{i:02d}', 0) for i in range(1, 32))
        self.total_hours = total
        self.total_days = round(total / 8, 1)

    def get_day_value(self, day):
        return getattr(self, f'day_{day:02d}', 0)

    def set_day_value(self, day, value):
        setattr(self, f'day_{day:02d}', value)

    @property
    def year(self):
        return int(self.year_month.split('-')[0])

    @property
    def month(self):
        return int(self.year_month.split('-')[1])

    @property
    def days_in_month(self):
        return calendar.monthrange(self.year, self.month)[1]

    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.year_month}"