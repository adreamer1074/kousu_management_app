from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.users.models import Department

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
    
    class PriorityChoices(models.TextChoices):
        LOW = 'low', '低'
        NORMAL = 'normal', '中'
        HIGH = 'high', '高'
        URGENT = 'urgent', '緊急'
    
    class StatusChoices(models.TextChoices):
        OPEN = 'open', '未着手'
        ESTIMATE = 'estimate', '見積'
        IN_PROGRESS = 'in_progress', '進行中'
        ON_HOLD = 'on_hold', '保留'
        CLOSED = 'closed', 'クローズ'
    
    class CaseClassificationChoices(models.TextChoices):
        DEVELOPMENT = 'development', '開発'
        MAINTENANCE = 'maintenance', '保守'
        CONSULTING = 'consulting', 'コンサルティング'
        SUPPORT = 'support', 'サポート'
        OTHER = 'other', 'その他'
    
    class BillingStatusChoices(models.TextChoices):
        ESTIMATE = 'estimate', '見積'
        LOST = 'lost', '失注'
        BILLED = 'billed', '請求済み'
        IN_PROGRESS = 'in_progress', '着手'
    
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
        choices=PriorityChoices.choices,
        default=PriorityChoices.NORMAL,
        verbose_name="優先度"
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
        verbose_name="ステータス"
    )
    
    case_classification = models.CharField(
        max_length=30,
        choices=CaseClassificationChoices.choices,
        default=CaseClassificationChoices.OTHER,
        verbose_name="分類"
    )
    
    billing_status = models.CharField(
        '請求ステータス',
        max_length=20,
        choices=BillingStatusChoices.choices,
        default=BillingStatusChoices.ESTIMATE,
        help_text='チケットの請求状況'
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
    is_active = models.BooleanField('アクティブ', default=True)

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
            'estimate': 'info',
            'in_progress': 'primary',
            'on_hold': 'warning',
            'closed': 'success',
        }
        return {
            'text': self.get_status_display(),
            'color': status_colors.get(self.status, 'secondary')
        }
    
    def get_case_classification_display_with_color(self):
        """案件分類の色付き表示"""
        classification_colors = {
            'development': 'primary',
            'maintenance': 'success',
            'consulting': 'info',
            'support': 'warning',
            'other': 'secondary',
        }
        return {
            'text': self.get_case_classification_display(),
            'color': classification_colors.get(self.case_classification, 'secondary')
        }
    
    def get_billing_status_display_with_color(self):
        """請求ステータスの色付き表示"""
        billing_colors = {
            'estimate': 'secondary',
            'lost': 'danger',
            'billed': 'success',
            'in_progress': 'primary',
        }
        return {
            'text': self.get_billing_status_display(),
            'color': billing_colors.get(self.billing_status, 'secondary')
        }

class ProjectDetail(models.Model):
    """案件詳細管理"""
    
    # ステータス選択肢
    STATUS_CHOICES = [
        ('planning', '計画中'),
        ('active', '進行中'),
        ('completed', '完了'),
        ('on_hold', '保留'),
        ('cancelled', 'キャンセル'),
        ('inspection_pending', '検収待ち'),
    ]
    
    # 案件分類選択肢
    CASE_CLASSIFICATION_CHOICES = [
        ('development', '開発'),
        ('maintenance', '保守'),
        ('consulting', 'コンサルティング'),
        ('support', 'サポート'),
        ('other', 'その他'),
    ]
    
    # 基本情報
    project = models.OneToOneField('Project', on_delete=models.CASCADE, related_name='detail')
    project_name = models.CharField('プロジェクト名', max_length=200)
    case_name = models.CharField('チケット名', max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='部署')
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='planning')
    case_classification = models.CharField('案件分類', max_length=20, choices=CASE_CLASSIFICATION_CHOICES, default='development')
    
    # 日程情報
    estimate_date = models.DateField('見積日', null=True, blank=True)
    order_date = models.DateField('受注日', null=True, blank=True)
    planned_end_date = models.DateField('終了日（予定）', null=True, blank=True)
    actual_end_date = models.DateField('終了日実績', null=True, blank=True)
    inspection_date = models.DateField('検収日', null=True, blank=True)
    
    # 金額情報（税別）
    budget_amount = models.DecimalField('使用可能金額（税別）', max_digits=12, decimal_places=0, default=0)
    billing_amount = models.DecimalField('請求金額（税別）', max_digits=12, decimal_places=0, default=0)
    outsourcing_cost = models.DecimalField('外注費（税別）', max_digits=12, decimal_places=0, default=0)
    
    # 工数情報（人日）
    estimated_workdays = models.DecimalField('見積工数（人日）', max_digits=8, decimal_places=2, default=0)
    used_workdays = models.DecimalField('使用工数（人日）', max_digits=8, decimal_places=2, default=0)
    newbie_workdays = models.DecimalField('新入社員使用工数（人日）', max_digits=8, decimal_places=2, default=0)
    
    # 計算フィールド（プロパティで動的計算）
    # remaining_workdays = 見積工数 - 使用工数
    # remaining_amount = 使用可能金額 - (使用工数 × 単価)
    # profit_rate = (請求金額 - 実際費用) / 請求金額 × 100
    # wip_amount = 仕掛中金額（人日×単価）
    
    # 取引先情報
    billing_destination = models.CharField('請求先', max_length=200, blank=True)
    billing_contact = models.CharField('請求先担当者', max_length=100, blank=True)
    mub_manager = models.CharField('MUB担当者', max_length=100, blank=True)
    
    # その他
    remarks = models.TextField('備考', blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        verbose_name = '案件詳細'
        verbose_name_plural = '案件詳細'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.project_name} - {self.case_name}"
    
    @property
    def remaining_workdays(self):
        """残工数（人日）"""
        return self.estimated_workdays - self.used_workdays

    @property
    def remaining_amount(self):
        """残金額（税抜）"""
        # 使用可能金額から実際使用金額を差し引く
        return max(self.budget_amount - self.billing_amount, 0)
    
    @property
    def profit_rate(self):
        """利益率"""
        if self.billing_amount > 0:
            # 利益 = 請求金額 - 外注費 - 人件費
            try:
                cost_master = self.get_cost_master()
                if cost_master:
                    # 人件費計算（月20日換算）
                    daily_rate = (cost_master.monthly_cost / 20) * 10000  # 万円単位に変換
                    personnel_cost = self.used_workdays * daily_rate
                else:
                    personnel_cost = 0
                
                # 利益 = 請求金額 - 外注費 - 人件費
                profit = self.billing_amount - self.outsourcing_cost - personnel_cost
                return (profit / self.billing_amount) * 100
            except:
                # コストマスターがない場合は外注費のみ考慮
                profit = self.billing_amount - self.outsourcing_cost
                return (profit / self.billing_amount) * 100
        return 0
    @property
    def wip_amount(self):
        """仕掛中金額（人日×単価）"""
        try:
            cost_master = self.get_cost_master()
            daily_rate = cost_master.monthly_cost / 20  # 月20日換算
            return self.used_workdays * daily_rate
        except:
            return 0
    
    @property
    def tax_included_billing_amount(self):
        """税込請求金額"""
        return self.billing_amount * 1.1  # 10%税込
    
    def get_cost_master(self):
        """コストマスターを取得"""
        from apps.cost_master.models import CostMaster
        return CostMaster.objects.filter(department=self.department).first()
    
    def get_total_cost(self):
        """総コスト計算"""
        try:
            cost_master = self.get_cost_master()
            personnel_cost = self.used_workdays * cost_master.monthly_cost / 20
            return personnel_cost + self.outsourcing_cost
        except:
            return self.outsourcing_cost
    
    def update_used_workdays_from_workloads(self, year_month=None):
        """工数入力データから使用工数を更新"""
        from apps.workloads.models import Workload
        
        if year_month:
            workloads = Workload.objects.filter(
                project=self.project,
                year_month=year_month
            )
        else:
            workloads = Workload.objects.filter(project=self.project)
        
        total_days = sum(w.total_days for w in workloads)
        self.used_workdays = total_days
        self.save()
        
        return total_days
    
    def get_outsourcing_cost_from_cost_master(self, year_month=None):
        """コストマスターの外注費を取得"""
        from apps.cost_master.models import OutsourcingCost
        
        # 関連するチケット（案件）の外注費を集計
        if not hasattr(self, 'ticket_id') or not self.ticket_id:
            return Decimal('0')
        
        try:
            # 指定年月または全期間の外注費を集計
            outsourcing_costs = OutsourcingCost.objects.filter(
                ticket_id=self.ticket_id,
                status='in_progress'  # 着手案件のみ
            )
            
            if year_month:
                outsourcing_costs = outsourcing_costs.filter(year_month=year_month)
            
            total_cost = sum(cost.total_cost for cost in outsourcing_costs)
            return total_cost
            
        except Exception as e:
            print(f"外注費取得エラー: {e}")
            return Decimal('0')
    
    @property
    def calculated_outsourcing_cost(self):
        """計算された外注費（現在月）"""
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')
        return self.get_outsourcing_cost_from_cost_master(current_month)
    
    @property
    def total_outsourcing_cost(self):
        """総外注費（全期間）"""
        return self.get_outsourcing_cost_from_cost_master()