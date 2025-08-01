from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

User = get_user_model()

class WorkloadAggregation(models.Model):
    """工数集計一覧テーブル"""
    
    class StatusChoices(models.TextChoices):
        PLANNING = 'planning', '計画中'
        IN_PROGRESS = 'in_progress', '進行中'
        BILLED = 'billed', '請求済み'
        COMPLETED = 'completed', '完了'
        INSPECTION_WAITING = 'inspection_waiting', '検収待ち'
        INSPECTED = 'inspected', '検収済み'
        ON_HOLD = 'on_hold', '保留'
        CANCELLED = 'cancelled', 'キャンセル（失注）'
    
    class CaseClassificationChoices(models.TextChoices):
        DEVELOPMENT = 'development', '開発'
        MAINTENANCE = 'maintenance', '保守'
        SUPPORT = 'support', 'サポート'
        CONSULTING = 'consulting', 'コンサルティング'
        OTHER = 'other', 'その他'
    
    # 基本情報 - 既存のProjectTicketを使用
    project_name = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        verbose_name='プロジェクト名',
        related_name='workload_aggregations_as_project'
    )
    case_name = models.ForeignKey(
        'projects.ProjectTicket',  # ProjectTicket
        on_delete=models.CASCADE,
        verbose_name='チケット名',
        related_name='workload_aggregations'
    )
    section = models.ForeignKey(
        'users.Section',
        on_delete=models.CASCADE,
        verbose_name='課名'
    )
    
    # 既存のフィールドはそのまま維持
    status = models.CharField(
        'ステータス',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNING
    )
    case_classification = models.CharField(
        '案件分類',
        max_length=20,
        choices=CaseClassificationChoices.choices,
        default=CaseClassificationChoices.DEVELOPMENT
    )
    
    # 日付関連
    estimate_date = models.DateField('見積日', null=True, blank=True)
    order_date = models.DateField('受注日', null=True, blank=True)
    planned_end_date = models.DateField('終了日（予定）', null=True, blank=True)
    actual_end_date = models.DateField('終了日実績（検収待ち）', null=True, blank=True)
    inspection_date = models.DateField('検収日', null=True, blank=True)
    
    # 金額関連（税別）
    available_amount = models.DecimalField(
        '使用可能金額（税別）',
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    billing_amount_excluding_tax = models.DecimalField(
        '請求金額（税別）',
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    outsourcing_cost_excluding_tax = models.DecimalField(
        '外注費（税別）',
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # 工数関連（人日）
    estimated_workdays = models.DecimalField(
        '見積工数（人日）',
        max_digits=8,
        decimal_places=1,
        default=Decimal('0.0'),
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    used_workdays = models.DecimalField(
        '使用工数（人日）',
        max_digits=8,
        decimal_places=1,
        default=Decimal('0.0'),
        validators=[MinValueValidator(Decimal('0.0'))],
        help_text='工数登録機能から自動計算'
    )
    newbie_workdays = models.DecimalField(
        '新入社員使用工数（人日）',
        max_digits=8,
        decimal_places=1,
        default=Decimal('0.0'),
        validators=[MinValueValidator(Decimal('0.0'))],
        help_text='ユーザーレベルがjuniorの工数を自動計算'
    )
    
    # 単価関連
    unit_cost_per_month = models.DecimalField(
        '単価（万円/月）',
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    billing_unit_cost_per_month = models.DecimalField(
        '請求単価（万円/月）',
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # 請求先情報
    billing_destination = models.CharField('請求先', max_length=200, blank=True)
    billing_contact = models.CharField('請求先担当者', max_length=100, blank=True)
    
    # 担当者
    mub_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='MUB担当者',
        related_name='managed_workload_aggregations'
    )
    
    # 備考
    remarks = models.TextField('備考', blank=True)
    
    # 管理情報
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_workload_aggregations',
        verbose_name='作成者'
    )
    
    class Meta:
        verbose_name = '工数集計'
        verbose_name_plural = '工数集計'
        ordering = ['-order_date', '-created_at']
    
    def __str__(self):
        return f"{self.project_name.name} - {self.case_name.title}"
    
    def calculate_workdays_from_workload(self):
        """工数登録機能から工数を自動計算（開発タイプは全期間対応版）"""
        from apps.workloads.models import Workload
        from decimal import Decimal
        from datetime import datetime, date
        import calendar
        
        # チケットに関連する工数を取得
        workloads = Workload.objects.filter(ticket=self.case_name)
        
        # チケットの分類を確認（開発タイプかどうか）
        is_development = self.case_classification == self.CaseClassificationChoices.DEVELOPMENT
        
        # 開発タイプでない場合のみ期間フィルターを適用
        if not is_development:
            # 保守・その他のタイプの場合は従来通り期間フィルター適用
            target_year_months = set()
            
            if self.order_date:
                start_date = self.order_date
            else:
                # デフォルトは現在年月から6ヶ月前
                start_date = date.today().replace(day=1)
            
            if self.actual_end_date:
                end_date = self.actual_end_date
            else:
                # デフォルトは現在年月
                end_date = date.today()
            
            # 対象年月のリストを作成
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                target_year_months.add(current_date.strftime('%Y-%m'))
                # 次の月へ
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            # 対象年月でフィルター（保守・その他のみ）
            if target_year_months:
                workloads = workloads.filter(year_month__in=target_year_months)
        
        # 開発タイプの場合はworkloadsをそのまま使用（全期間対象）
        
        # 一般使用工数と新入社員工数を分離
        regular_workdays = Decimal('0.0')
        newbie_workdays = Decimal('0.0')
        
        for workload in workloads:
            # ユーザーのemployee_levelを確認
            is_junior = False
            if hasattr(workload.user, 'employee_level') and workload.user.employee_level == 'junior':
                is_junior = True
            
            # 各日の工数を合計
            workload_year_month = workload.year_month
            year, month = map(int, workload_year_month.split('-'))
            
            # その月の日数を取得
            days_in_month = calendar.monthrange(year, month)[1]
            
            for day in range(1, days_in_month + 1):
                # 開発タイプの場合は日付範囲チェックを完全にスキップ
                if not is_development:
                    # 保守・その他のタイプの場合のみ日付範囲チェック
                    current_day = date(year, month, day)
                    if self.order_date and current_day < self.order_date:
                        continue
                    if self.actual_end_date and current_day > self.actual_end_date:
                        continue
                
                # その日の工数を取得
                day_hours = workload.get_day_value(day)
                
                # 工数の分類
                if is_junior:
                    newbie_workdays += Decimal(str(day_hours))
                else:
                    regular_workdays += Decimal(str(day_hours))
        
        # 時間を人日に変換（8時間=1人日として計算）
        self.used_workdays = regular_workdays / 8
        self.newbie_workdays = newbie_workdays / 8
        
        # デバッグ情報を返す
        all_workloads_count = Workload.objects.filter(ticket=self.case_name).count()
        filtered_workloads_count = workloads.count()
        
        debug_info = {
            'チケット分類': self.get_case_classification_display(),
            '開発タイプ判定': is_development,
            '期間フィルター適用': not is_development,
            '全工数レコード数': all_workloads_count,
            '対象工数レコード数': filtered_workloads_count,
            '一般工数（時間）': float(regular_workdays),
            '新入社員工数（時間）': float(newbie_workdays),
            '一般工数（人日）': float(self.used_workdays),
            '新入社員工数（人日）': float(self.newbie_workdays),
        }
        
        if is_development:
            debug_info['適用期間'] = "開発タイプのため全期間対象"
            debug_info['年月フィルター'] = "なし（全期間）"
        else:
            if self.order_date and self.actual_end_date:
                debug_info['適用期間'] = f"{self.order_date} ～ {self.actual_end_date}"
            else:
                debug_info['適用期間'] = "受注日・終了日未設定のため制限なし"
            
            # 対象年月をデバッグ情報に追加
            if 'target_year_months' in locals():
                debug_info['対象年月リスト'] = sorted(list(target_year_months))
            else:
                debug_info['対象年月リスト'] = "フィルターなし"
        
        return {
            'used_workdays': self.used_workdays,
            'newbie_workdays': self.newbie_workdays,
            'total_workdays': self.used_workdays + self.newbie_workdays,
            'debug_info': debug_info
        }
    
    # 既存のpropertyメソッドはそのまま維持
    @property
    def total_used_workdays(self):
        """使用工数合計（日）"""
        return self.used_workdays + self.newbie_workdays
    
    @property
    def remaining_workdays(self):
        """残工数（人日）"""
        return max(self.estimated_workdays - self.total_used_workdays, Decimal('0.0'))
    
    @property
    def remaining_amount(self):
        """残金額（税抜）"""
        return max(self.available_amount - self.billing_amount_excluding_tax, Decimal('0'))
    
    @property
    def profit_rate(self):
        """利益率"""
        if self.billing_amount_excluding_tax > 0:
            profit = self.billing_amount_excluding_tax - self.outsourcing_cost_excluding_tax
            return round((profit / self.billing_amount_excluding_tax) * 100, 1)
        return Decimal('0.0')
    
    @property
    def wip_amount(self):
        """仕掛中金額（人日×単価）"""
        return self.used_workdays * (self.unit_cost_per_month / 20)  # 月20日計算
    
    @property
    def wip_amount_partner(self):
        """仕掛中合計（協力会社）"""
        return self.newbie_workdays * (self.unit_cost_per_month / 20)
    
    @property
    def tax_excluded_billing_amount(self):
        """税抜請求金額（表示用）"""
        return self.billing_amount_excluding_tax


class ReportExport(models.Model):
    """レポートエクスポート管理モデル"""
    
    class ExportTypeChoices(models.TextChoices):
        WORKLOAD_AGGREGATION = 'workload_aggregation', '工数集計レポート'
        WORKLOAD_DETAIL = 'workload_detail', '工数詳細レポート'
        PROJECT_SUMMARY = 'project_summary', 'プロジェクト概要レポート'
        USER_WORKLOAD = 'user_workload', 'ユーザー別工数レポート'
    
    class ExportFormatChoices(models.TextChoices):
        EXCEL = 'excel', 'Excel (.xlsx)'
        CSV = 'csv', 'CSV (.csv)'
        PDF = 'pdf', 'PDF (.pdf)'
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', '処理待ち'
        PROCESSING = 'processing', '処理中'
        COMPLETED = 'completed', '完了'
        FAILED = 'failed', '失敗'
    
    # 基本情報
    export_type = models.CharField(
        'エクスポート種類',
        max_length=50,
        choices=ExportTypeChoices.choices,
        default=ExportTypeChoices.WORKLOAD_AGGREGATION
    )
    export_format = models.CharField(
        'エクスポート形式',
        max_length=20,
        choices=ExportFormatChoices.choices,
        default=ExportFormatChoices.EXCEL
    )
    
    # ファイル情報
    file_name = models.CharField('ファイル名', max_length=255)
    file_path = models.CharField('ファイルパス', max_length=500, blank=True)
    file_size = models.PositiveIntegerField('ファイルサイズ（バイト）', null=True, blank=True)
    file_s3_url = models.URLField('S3ファイルURL', blank=True, null=True)
    
    # フィルター条件（JSON形式で保存）
    filter_conditions = models.JSONField(
        'フィルター条件',
        default=dict,
        blank=True,
        help_text='エクスポート時のフィルター条件をJSON形式で保存'
    )
    
    # ステータス
    status = models.CharField(
        'ステータス',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    
    # 処理情報
    total_records = models.PositiveIntegerField('総レコード数', null=True, blank=True)
    exported_records = models.PositiveIntegerField('エクスポート済みレコード数', null=True, blank=True)
    error_message = models.TextField('エラーメッセージ', blank=True)
    
    # 日時情報
    requested_at = models.DateTimeField('リクエスト日時', auto_now_add=True)
    started_at = models.DateTimeField('開始日時', null=True, blank=True)
    completed_at = models.DateTimeField('完了日時', null=True, blank=True)
    expires_at = models.DateTimeField('有効期限', null=True, blank=True)
    
    # ユーザー情報
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requested_exports',
        verbose_name='リクエストユーザー'
    )
    
    # 追加情報
    description = models.TextField('説明', blank=True)
    is_public = models.BooleanField('公開', default=False, help_text='他のユーザーがダウンロード可能か')
    download_count = models.PositiveIntegerField('ダウンロード回数', default=0)
    
    class Meta:
        verbose_name = 'レポートエクスポート'
        verbose_name_plural = 'レポートエクスポート'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['requested_by', '-requested_at']),
            models.Index(fields=['status', '-requested_at']),
            models.Index(fields=['export_type', '-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.get_export_type_display()} - {self.file_name} ({self.get_status_display()})"
    
    @property
    def is_downloadable(self):
        """ダウンロード可能かどうか"""
        return self.status == self.StatusChoices.COMPLETED and self.file_path
    
    @property
    def processing_time(self):
        """処理時間（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_expired(self):
        """有効期限切れかどうか"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    def get_file_size_display(self):
        """ファイルサイズの表示用文字列"""
        if not self.file_size:
            return "不明"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def increment_download_count(self):
        """ダウンロード回数をインクリメント"""
        self.download_count += 1
        self.save(update_fields=['download_count'])