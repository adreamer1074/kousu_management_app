from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class ProjectStatus(models.TextChoices):
    """プロジェクトステータス"""
    PLANNING = 'planning', '計画中'
    ACTIVE = 'active', '進行中'
    ON_HOLD = 'on_hold', '保留中'
    COMPLETED = 'completed', '完了'
    CANCELLED = 'cancelled', 'キャンセル'

class ProjectPriority(models.TextChoices):
    """プロジェクト優先度"""
    LOW = 'low', '低'
    MEDIUM = 'medium', '中'
    HIGH = 'high', '高'
    URGENT = 'urgent', '緊急'

class Project(models.Model):
    """プロジェクトモデル"""
    name = models.CharField(
        max_length=200,
        verbose_name="プロジェクト名"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="プロジェクトコード",
        help_text="例: PROJ-2025-001"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="説明"
    )
    client = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="クライアント"
    )
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PLANNING,
        verbose_name="ステータス"
    )
    priority = models.CharField(
        max_length=20,
        choices=ProjectPriority.choices,
        default=ProjectPriority.MEDIUM,
        verbose_name="優先度"
    )
    start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="開始予定日"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="終了予定日"
    )
    actual_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="実際の開始日"
    )
    actual_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="実際の終了日"
    )
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        blank=True,
        null=True,
        verbose_name="予算（円）"
    )
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="見積工数（時間）"
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects',
        verbose_name="プロジェクトマネージャー"
    )
    department = models.ForeignKey(
        'users.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name="担当部署"
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
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
        verbose_name="作成者"
    )

    class Meta:
        verbose_name = "プロジェクト"
        verbose_name_plural = "プロジェクト"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self):
        """期限切れかどうか"""
        if not self.end_date:
            return False
        
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
            return False
            
        return self.end_date < today

    @property
    def progress_percentage(self):
        """進捗率を計算"""
        if not self.start_date or not self.end_date:
            return 0
        
        from django.utils import timezone
        today = timezone.now().date()
        
        if today < self.start_date:
            return 0
        elif today > self.end_date:
            return 100
        
        total_days = (self.end_date - self.start_date).days
        elapsed_days = (today - self.start_date).days
        
        if total_days == 0:
            return 100
        
        return min(100, max(0, int((elapsed_days / total_days) * 100)))

    @property
    def total_workload_hours(self):
        """総工数時間を計算"""
        from apps.workloads.models import Workload
        return Workload.objects.filter(project=self).aggregate(
            total=models.Sum('hours')
        )['total'] or 0

    @property
    def member_count(self):
        """プロジェクトメンバー数"""
        return self.members.filter(is_active=True).count()

class ProjectMember(models.Model):
    """プロジェクトメンバーモデル"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="プロジェクト"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_memberships',
        verbose_name="ユーザー"
    )
    role = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="役割",
        help_text="例: 開発者、テスター、デザイナー"
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=0,
        blank=True,
        null=True,
        verbose_name="時間単価（円）"
    )
    join_date = models.DateField(
        verbose_name="参加日"
    )
    leave_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="離脱日"
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
        verbose_name = "プロジェクトメンバー"
        verbose_name_plural = "プロジェクトメンバー"
        unique_together = ['project', 'user']
        ordering = ['join_date']

    def __str__(self):
        return f"{self.project.name} - {self.user.username}"

    @property
    def total_hours(self):
        """このメンバーの総工数時間"""
        from apps.workloads.models import Workload
        return Workload.objects.filter(
            project=self.project,
            user=self.user
        ).aggregate(total=models.Sum('hours'))['total'] or 0

class ProjectPhase(models.Model):
    """プロジェクトフェーズモデル"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='phases',
        verbose_name="プロジェクト"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="フェーズ名"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="説明"
    )
    start_date = models.DateField(
        verbose_name="開始予定日"
    )
    end_date = models.DateField(
        verbose_name="終了予定日"
    )
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="見積工数（時間）"
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name="順序"
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="完了"
    )
    completion_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="完了日"
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
        verbose_name = "プロジェクトフェーズ"
        verbose_name_plural = "プロジェクトフェーズ"
        ordering = ['order', 'start_date']
        unique_together = ['project', 'name']

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    @property
    def duration_days(self):
        """フェーズの期間（日数）"""
        return (self.end_date - self.start_date).days + 1

    @property
    def total_hours(self):
        """このフェーズの総工数時間"""
        from apps.workloads.models import Workload
        return Workload.objects.filter(
            project=self.project,
            phase=self
        ).aggregate(total=models.Sum('hours'))['total'] or 0