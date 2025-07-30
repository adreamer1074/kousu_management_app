from django import forms
from django.contrib.auth import get_user_model
from datetime import date, datetime
from .models import WorkloadAggregation
from apps.users.models import Department, Section
from apps.projects.models import Project, ProjectTicket

User = get_user_model()

class WorkloadAggregationForm(forms.ModelForm):
    """工数集計フォーム（ProjectTicket対応版）"""
    
    # 工数自動計算ボタン用フィールド
    auto_calculate_workdays = forms.BooleanField(
        label='工数を自動計算する',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = WorkloadAggregation
        fields = [
            # 基本情報（プロジェクト・チケット）
            'project_name', 'case_name', 'section', 'status', 'case_classification',
            # 日付関連
            'estimate_date', 'order_date', 'planned_end_date', 'actual_end_date', 'inspection_date',
            # 金額関連
            'available_amount', 'billing_amount_excluding_tax', 'outsourcing_cost_excluding_tax',
            # 工数関連（自動計算対応）
            'estimated_workdays', 'used_workdays', 'newbie_workdays',
            # 単価関連
            'unit_cost_per_month', 'billing_unit_cost_per_month',
            # 請求先・担当者
            'billing_destination', 'billing_contact', 'mub_manager',
            # 備考
            'remarks'
        ]
        widgets = {
            # 基本情報
            'project_name': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_project_name'
            }),
            'case_name': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_case_name'
            }),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'case_classification': forms.Select(attrs={'class': 'form-select'}),
            
            # 日付関連
            'estimate_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'inspection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            
            # 金額関連
            'available_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': '0'
            }),
            'billing_amount_excluding_tax': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': '0'
            }),
            'outsourcing_cost_excluding_tax': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': '0'
            }),
            
            # 工数関連（自動計算対応）
            'estimated_workdays': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': '0.0'
            }),
            'used_workdays': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': '0.0',
                'readonly': True,
                'style': 'background-color: #f8f9fa; border: 1px solid #ced4da;'
            }),
            'newbie_workdays': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': '0.0',
                'readonly': True,
                'style': 'background-color: #f8f9fa; border: 1px solid #ced4da;'
            }),
            
            # 単価関連
            'unit_cost_per_month': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'billing_unit_cost_per_month': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            
            # 請求先・担当者
            'billing_destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請求先を入力してください'
            }),
            'billing_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請求先担当者を入力してください'
            }),
            'mub_manager': forms.Select(attrs={'class': 'form-select'}),
            
            # 備考
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '備考があれば記載してください'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # プロジェクト名の選択肢を設定
        self.fields['project_name'].queryset = Project.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['project_name'].empty_label = "プロジェクトを選択してください"
        
        # チケット名の選択肢を初期設定
        if self.instance.pk and self.instance.project_name:
            # 編集時：選択されたプロジェクトのチケットのみ表示
            self.fields['case_name'].queryset = ProjectTicket.objects.filter(
                project=self.instance.project_name,
                is_active=True
            ).order_by('title')
        elif 'project_name' in self.data:
            # フォーム送信時：選択されたプロジェクトのチケットのみ表示
            try:
                project_id = int(self.data.get('project_name'))
                self.fields['case_name'].queryset = ProjectTicket.objects.filter(
                    project_id=project_id,
                    is_active=True
                ).order_by('title')
            except (ValueError, TypeError):
                self.fields['case_name'].queryset = ProjectTicket.objects.none()
        else:
            # 新規作成時：プロジェクト未選択のため空
            self.fields['case_name'].queryset = ProjectTicket.objects.none()
        
        self.fields['case_name'].empty_label = "チケット（案件）を選択してください"
        
        # 課名の選択肢を設定
        self.fields['section'].queryset = Section.objects.filter(
            is_active=True
        ).select_related('department').order_by('department__name', 'name')
        self.fields['section'].empty_label = "課を選択してください"

        # MUB担当者の選択肢を設定
        self.fields['mub_manager'].queryset = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['mub_manager'].empty_label = "MUB担当者を選択（任意）"
        
        # フィールドのヘルプテキスト設定
        self.fields['project_name'].help_text = '対象プロジェクトを選択してください'
        self.fields['case_name'].help_text = 'プロジェクト内のチケット（案件）を選択してください'
        self.fields['case_classification'].help_text = '案件の分類を選択してください（開発の場合は全期間の工数が計算されます）'
        self.fields['used_workdays'].help_text = '工数登録機能から自動計算されます'
        self.fields['newbie_workdays'].help_text = 'ユーザーレベルがjuniorの工数を自動計算'
        self.fields['auto_calculate_workdays'].help_text = 'チェックすると保存時に工数を自動計算します'

        # チケット選択時の外注費自動設定用のJavaScriptを追加
        self.fields['case_name'].widget.attrs.update({
            'data-auto-fetch-outsourcing': 'true'
        })
    
    def clean(self):
        """フォーム全体のバリデーション"""
        cleaned_data = super().clean()
        
        # チケット選択時に外注費を自動設定
        case_name = cleaned_data.get('case_name')
        if case_name and hasattr(case_name, 'id'):
            # 外注費を自動計算
            from apps.cost_master.models import OutsourcingCost
            from datetime import datetime
            
            current_month = datetime.now().strftime('%Y-%m')
            outsourcing_costs = OutsourcingCost.objects.filter(
                ticket_id=case_name.id,
                status='in_progress',
                year_month=current_month
            )
            
            total_outsourcing_cost = sum(cost.total_cost for cost in outsourcing_costs)
            
            # フォームデータに外注費を設定（JavaScript側で処理するため、ここでは参考値として計算）
            cleaned_data['calculated_outsourcing_cost'] = total_outsourcing_cost
        
        # プロジェクトとチケットの整合性チェック
        project_name = cleaned_data.get('project_name')
        case_name = cleaned_data.get('case_name')
        
        if project_name and case_name:
            if case_name.project != project_name:
                self.add_error('case_name', '選択されたチケットは選択されたプロジェクトに属していません。')
        
        # 日付の妥当性チェック
        estimate_date = cleaned_data.get('estimate_date')
        order_date = cleaned_data.get('order_date')
        planned_end_date = cleaned_data.get('planned_end_date')
        actual_end_date = cleaned_data.get('actual_end_date')
        inspection_date = cleaned_data.get('inspection_date')
        
        if estimate_date and order_date and estimate_date > order_date:
            self.add_error('order_date', '受注日は見積日以降の日付を設定してください。')
        
        if order_date and planned_end_date and order_date > planned_end_date:
            self.add_error('planned_end_date', '終了日（予定）は受注日以降の日付を設定してください。')
        
        if actual_end_date and inspection_date and actual_end_date > inspection_date:
            self.add_error('inspection_date', '検収日は終了日実績以降の日付を設定してください。')
        
        # 金額の妥当性チェック
        available_amount = cleaned_data.get('available_amount')
        billing_amount = cleaned_data.get('billing_amount_excluding_tax')
        outsourcing_cost = cleaned_data.get('outsourcing_cost_excluding_tax')
        
        if available_amount and available_amount < 0:
            self.add_error('available_amount', '予算金額は0以上で入力してください。')
        
        if billing_amount and billing_amount < 0:
            self.add_error('billing_amount_excluding_tax', '請求金額は0以上で入力してください。')
        
        if outsourcing_cost and outsourcing_cost < 0:
            self.add_error('outsourcing_cost_excluding_tax', '外注費は0以上で入力してください。')
        
        return cleaned_data

    def save(self, commit=True):
        """保存処理"""
        instance = super().save(commit=False)
        
        # 工数の自動計算を実行（新規登録時も含む）
        if self.cleaned_data.get('auto_calculate_workdays', False) and instance.case_name:
            try:
                # デバッグ情報を出力（開発時のみ）
                import logging
                logger = logging.getLogger(__name__)
                
                # 案件分類が設定されているかチェック
                if not instance.case_classification:
                    # case_nameから案件分類を自動設定
                    if hasattr(instance.case_name, 'case_classification'):
                        instance.case_classification = instance.case_name.case_classification
                    else:
                        # デフォルトを開発に設定
                        instance.case_classification = instance.CaseClassificationChoices.DEVELOPMENT
                
                logger.info(f"工数計算開始: チケット={instance.case_name.title}, 分類={instance.get_case_classification_display()}")
                
                # 工数計算実行
                workdays_data = instance.calculate_workdays_from_workload()
                instance.used_workdays = workdays_data['used_workdays']
                instance.newbie_workdays = workdays_data['newbie_workdays']
                
                # 計算結果をログ出力
                logger.info(f"工数計算結果: {workdays_data['debug_info']}")
                print(f"=== 工数計算結果 ===")
                print(f"チケット: {instance.case_name.title}")
                print(f"分類: {workdays_data['debug_info']['チケット分類']}")
                print(f"開発タイプ判定: {workdays_data['debug_info']['開発タイプ判定']}")
                print(f"対象工数レコード数: {workdays_data['debug_info']['対象工数レコード数']}")
                print(f"一般工数（人日）: {workdays_data['debug_info']['一般工数（人日）']}")
                print(f"新入社員工数（人日）: {workdays_data['debug_info']['新入社員工数（人日）']}")
                print(f"適用期間: {workdays_data['debug_info']['適用期間']}")
                print("=====================")
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"工数自動計算エラー: {str(e)}")
                print(f"工数自動計算エラー: {str(e)}")
                # エラーが発生してもフォーム全体は保存する
                pass
    
        if commit:
            instance.save()
        return instance

# フィルターフォームも更新
class WorkloadAggregationFilterForm(forms.Form):
    """工数集計フィルターフォーム（ProjectTicket対応版）"""
    
    project_name = forms.ModelChoiceField(
        label='プロジェクト名',
        queryset=Project.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="全てのプロジェクト",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    case_name = forms.ModelChoiceField(
        label='チケット名',
        queryset=ProjectTicket.objects.select_related('project').filter(is_active=True).order_by('project__name', 'title'),
        required=False,
        empty_label="全てのチケット",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    section = forms.ModelChoiceField(
        label='課名',
        queryset=Section.objects.filter(is_active=True).select_related('department').order_by('department__name', 'name'),
        required=False,
        empty_label="全ての課",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label='ステータス',
        choices=[('', '全てのステータス')] + WorkloadAggregation.StatusChoices.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    case_classification = forms.ChoiceField(
        label='案件分類',
        choices=[('', '全ての案件分類')] + WorkloadAggregation.CaseClassificationChoices.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    mub_manager = forms.ModelChoiceField(
        label='MUB担当者',
        queryset=User.objects.filter(is_active=True).order_by('last_name', 'first_name'),
        required=False,
        empty_label="全ての担当者",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        label='検索',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'プロジェクト名・チケット名・備考で検索'
        })
    )