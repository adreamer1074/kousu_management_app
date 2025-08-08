from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import date
from decimal import Decimal
from apps.users.models import CustomUser, Department
from apps.projects.models import Project, ProjectTicket

class BusinessPartner(models.Model):
    """ビジネスパートナー（BP）管理"""
    
    # 基本情報
    name = models.CharField('氏名', max_length=100)
    email = models.EmailField('メールアドレス', blank=True)
    phone = models.CharField('電話番号', max_length=20, blank=True)
    company = models.CharField('所属会社', max_length=200, blank=True)
    
    # 契約情報
    hourly_rate = models.DecimalField(
        '時間単価（円）',
        max_digits=8,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # 参加プロジェクト（多対多関係）
    projects = models.ManyToManyField(
        Project,
        verbose_name='参加プロジェクト',
        blank=True,
        help_text='このBPが参加可能なプロジェクト'
    )
    
    # ステータス
    is_active = models.BooleanField('有効', default=True)
    
    # 管理情報
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='作成者'
    )
    
    # 備考
    notes = models.TextField('備考', blank=True)
    
    class Meta:
        verbose_name = 'ビジネスパートナー'
        verbose_name_plural = 'ビジネスパートナー'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (¥{self.hourly_rate:,.0f}/時間)"
    
    def get_available_tickets(self):
        """参加プロジェクトのアクティブなチケットを取得"""
        return ProjectTicket.objects.filter(
            project__in=self.projects.all(),
            is_active=True
        )


class OutsourcingCost(models.Model):
    """外注費集計"""
    
    # ステータス選択肢
    STATUS_CHOICES = [
        ('not_started', '未着手'),
        ('in_progress', '着手'),
    ]
    
    # チケット分類選択肢
    CASE_CLASSIFICATION_CHOICES = [
        ('development', '開発'),
        ('maintenance', '保守'),
    ]
    
    # 年月
    year_month = models.CharField(
        '年月',
        max_length=7,  # YYYY-MM形式
        help_text='YYYY-MM形式で入力'
    )
    
    # ビジネスパートナー
    business_partner = models.ForeignKey(
        BusinessPartner,
        on_delete=models.CASCADE,
        verbose_name='ビジネスパートナー'
    )
    
    # プロジェクト・チケット
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name='プロジェクト名'
    )
    ticket = models.ForeignKey(
        ProjectTicket,
        on_delete=models.CASCADE,
        verbose_name='チケット名'
    )
    
    # ステータス・分類
    status = models.CharField(
        'ステータス',
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    case_classification = models.CharField(
        '分類',
        max_length=20,
        choices=CASE_CLASSIFICATION_CHOICES,
        default='development'
    )
    
    # 作業時間
    work_hours = models.DecimalField(
        '時間',
        max_digits=8,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='作業時間を入力'
    )
    
    # 単価（BPから自動取得）
    hourly_rate = models.DecimalField(
        '単価（円）',
        max_digits=8,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='ビジネスパートナーの単価から自動設定'
    )
    
    # 外注費（自動計算）
    total_cost = models.DecimalField(
        '外注費',
        max_digits=10,
        decimal_places=0,
        default=Decimal('0'),
        help_text='ステータスが着手の場合のみ自動計算'
    )
    
    # 備考
    notes = models.TextField('備考', blank=True)
    
    # 管理情報
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='作成者'
    )
    is_active = models.BooleanField(default=True, verbose_name='有効フラグ')

    
    class Meta:
        db_table = 'outsourcing_costs'
        verbose_name = '外注費'
        verbose_name_plural = '外注費'
        ordering = ['-year_month', 'business_partner__name']
        unique_together = [
            ['year_month', 'business_partner', 'project', 'ticket']
        ]
    
    def __str__(self):
        return f"{self.year_month} - {self.business_partner.name} - {self.project.name}"
    
    def soft_delete(self):
        """論理削除"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def save(self, *args, **kwargs):
        """保存時の自動処理"""
        # BPの単価を自動設定
        if self.business_partner_id:
            self.hourly_rate = self.business_partner.hourly_rate
        
        # 外注費の自動計算（着手の場合のみ）
        if self.status == 'in_progress':
            self.total_cost = self.work_hours * self.hourly_rate
        else:
            self.total_cost = Decimal('0')
        
        super().save(*args, **kwargs)
    
    @property
    def calculated_cost(self):
        """計算された外注費を取得"""
        if self.status == 'in_progress':
            return self.work_hours * self.hourly_rate
        return Decimal('0')


class OutsourcingCostSummary(models.Model):
    """外注費月次集計"""
    
    year_month = models.CharField(
        '年月',
        max_length=7,
        unique=True,
        help_text='YYYY-MM形式'
    )
    
    # 集計値
    total_hours = models.DecimalField(
        '総作業時間',
        max_digits=10,
        decimal_places=1,
        default=Decimal('0')
    )
    total_cost = models.DecimalField(
        '総外注費',
        max_digits=12,
        decimal_places=0,
        default=Decimal('0')
    )
    total_records = models.IntegerField(
        '総レコード数',
        default=0
    )
    in_progress_records = models.IntegerField(
        '着手件数',
        default=0
    )
    not_started_records = models.IntegerField(
        '未着手件数',
        default=0
    )
    
    # 管理情報
    last_calculated = models.DateTimeField('最終計算日時', auto_now=True)
    
    class Meta:
        verbose_name = '外注費月次集計'
        verbose_name_plural = '外注費月次集計'
        ordering = ['-year_month']
    
    def __str__(self):
        return f"{self.year_month} - ¥{self.total_cost:,.0f}"
    
    @classmethod
    def calculate_summary(cls, year_month):
        """指定年月の集計を計算"""
        outsourcing_costs = OutsourcingCost.objects.filter(year_month=year_month)
        
        summary, created = cls.objects.get_or_create(
            year_month=year_month,
            defaults={
                'total_hours': Decimal('0'),
                'total_cost': Decimal('0'),
                'total_records': 0,
                'in_progress_records': 0,
                'not_started_records': 0,
            }
        )
        
        # 集計計算
        summary.total_records = outsourcing_costs.count()
        summary.in_progress_records = outsourcing_costs.filter(status='in_progress').count()
        summary.not_started_records = outsourcing_costs.filter(status='not_started').count()
        
        # 着手案件のみ集計
        in_progress_costs = outsourcing_costs.filter(status='in_progress')
        summary.total_hours = sum(cost.work_hours for cost in in_progress_costs)
        summary.total_cost = sum(cost.total_cost for cost in in_progress_costs)
        
        summary.save()
        return summary


class CostMaster(models.Model):
    """コストマスター"""
    
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name='部署',
        related_name='cost_masters'
    )
    
    # 月額コスト（円）
    monthly_cost = models.DecimalField(
        '月額コスト（円）',
        max_digits=10,
        decimal_places=0,
        default=750000,  # 75万円
        help_text='1か月あたりの人件費（円）'
    )
    
    # 日単価（円）
    daily_rate = models.DecimalField(
        '日単価（円）',
        max_digits=8,
        decimal_places=0,
        default=50000,  # 5万円
        help_text='1日あたりの単価（円）'
    )
    
    # 有効期間
    valid_from = models.DateField('有効開始日')
    valid_to = models.DateField('有効終了日', null=True, blank=True)
    
    # フラグ
    is_active = models.BooleanField('有効', default=True)
    
    # メタデータ
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        verbose_name = 'コストマスター'
        verbose_name_plural = 'コストマスター'
        ordering = ['-valid_from']
    
    def __str__(self):
        return f"{self.department.name} - {self.daily_rate:,}円/日"
    
    @property
    def daily_rate_from_monthly(self):
        """月額から日単価を計算"""
        return self.monthly_cost / 20  # 月20日稼働として計算