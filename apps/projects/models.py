from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class Project(models.Model):
    """プロジェクトモデル"""
    STATUS_CHOICES = [
        ('planning', '計画中'),
        ('active', '進行中'),
        ('paused', '一時停止'),
        ('completed', '完了'),
        ('cancelled', 'キャンセル'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="プロジェクト名")
    description = models.TextField(blank=True, default="", verbose_name="説明")
    client = models.CharField(
        max_length=200, 
        blank=True, 
        default="",
        verbose_name="クライアント"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='planning',
        verbose_name="ステータス"
    )
    start_date = models.DateField(blank=True, null=True, verbose_name="開始日")
    end_date = models.DateField(blank=True, null=True, verbose_name="終了日")
    budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="予算"
    )
    assigned_section = models.ForeignKey(
        'users.Section',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="担当課",
        related_name='projects'
    )
    assigned_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='assigned_projects',
        verbose_name="マネージャー"
    )
    is_active = models.BooleanField(default=True, verbose_name="有効")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "プロジェクト"
        verbose_name_plural = "プロジェクト"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.pk})
    
    @property
    def period_display(self):
        """期間の表示用プロパティ"""
        if self.start_date and self.end_date:
            return f"{self.start_date} ～ {self.end_date}"
        elif self.start_date:
            return f"{self.start_date} ～"
        elif self.end_date:
            return f"～ {self.end_date}"
        return "未設定"
    
    @property
    def assigned_users_display(self):
        """担当者の表示用プロパティ"""
        users = self.assigned_users.all()
        if users:
            return ", ".join([user.get_full_name() or user.username for user in users[:3]])
        return "未設定"
    
    def get_status_display_with_color(self):
        """ステータスの色付き表示"""
        status_colors = {
            'planning': 'secondary',
            'active': 'primary',
            'paused': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return {
            'text': self.get_status_display(),
            'color': status_colors.get(self.status, 'secondary')
        }

class ProjectTicket(models.Model):
    """プロジェクトチケットモデル"""
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '中'),
        ('high', '高'),
        ('urgent', '緊急'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'オープン'),
        ('in_progress', '進行中'),
        ('review', 'レビュー中'),
        ('closed', 'クローズ'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="プロジェクト"
    )
    title = models.CharField(max_length=200, verbose_name="タイトル")
    description = models.TextField(blank=True, verbose_name="説明")
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name="優先度"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name="ステータス"
    )
    assigned_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="担当者"
    )
    due_date = models.DateField(blank=True, null=True, verbose_name="期限")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "チケット"
        verbose_name_plural = "チケット"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.title}"
    
    def get_priority_display_with_color(self):
        """優先度の色付き表示"""
        priority_colors = {
            'low': 'success',
            'normal': 'info',
            'high': 'warning',
            'urgent': 'danger',
        }
        return {
            'text': self.get_priority_display(),
            'color': priority_colors.get(self.priority, 'info')
        }
    
    def get_status_display_with_color(self):
        """ステータスの色付き表示"""
        status_colors = {
            'open': 'secondary',
            'in_progress': 'primary',
            'review': 'warning',
            'closed': 'success',
        }
        return {
            'text': self.get_status_display(),
            'color': status_colors.get(self.status, 'secondary')
        }