from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Workload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workloads')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='workloads')
    department = models.ForeignKey('departments.Department', on_delete=models.CASCADE, related_name='workloads')
    year_month = models.CharField(max_length=7)  # YYYY-MM
    # 1日〜31日分の工数
    day_01 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_02 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_03 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_04 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_05 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_06 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_07 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_08 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_09 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_10 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_11 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_12 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_13 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_14 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_15 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_16 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_17 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_18 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_19 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_20 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_21 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_22 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_23 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_24 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_25 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_26 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_27 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_28 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_29 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_30 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    day_31 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.year_month})"