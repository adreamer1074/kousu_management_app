from django import forms
from django.contrib.auth import get_user_model
from datetime import date, datetime
from .models import WorkloadAggregation
from apps.users.models import Department, Section
from apps.projects.models import Project, ProjectTicket  # 既存のProjectTicketを使用

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
            # 基本情報
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
            'project_name': forms.Select(attrs={'class': 'form-select'}),
            'case_name': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'case_classification': forms.Select(attrs={'class': 'form-select'}),
            
            # 日付関連
            'estimate_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'inspection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            
            # 金額関連（税別）
            'available_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'billing_amount_excluding_tax': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'outsourcing_cost_excluding_tax': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            
            # 工数関連（自動計算対応）
            'estimated_workdays': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'placeholder': '0.0'}),
            'used_workdays': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': '0.0',
                'readonly': True,
                'style': 'background-color: #e9ecef;'
            }),
            'newbie_workdays': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': '0.0',
                'readonly': True,
                'style': 'background-color: #e9ecef;'
            }),
            
            # 単価関連
            'unit_cost_per_month': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'billing_unit_cost_per_month': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            
            # 請求先・担当者
            'billing_destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請求先を入力してください'}),
            'billing_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請求先担当者を入力してください'}),
            'mub_manager': forms.Select(attrs={'class': 'form-select'}),
            
            # 備考
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '備考があれば記載してください'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # プロジェクト名（プロジェクトリストから選択）
        self.fields['project_name'].queryset = Project.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['project_name'].empty_label = "プロジェクトを選択してください"
        
        # 案件名（ProjectTicketリストから選択）
        self.fields['case_name'].queryset = ProjectTicket.objects.select_related('project').order_by('project__name', 'title')
        self.fields['case_name'].empty_label = "チケット（案件）を選択してください"
        
        # プロジェクト選択時にチケットをフィルター
        if 'project_name' in self.data:
            try:
                project_id = int(self.data.get('project_name'))
                self.fields['case_name'].queryset = ProjectTicket.objects.filter(
                    project_id=project_id
                ).order_by('title')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.project_name:
            self.fields['case_name'].queryset = ProjectTicket.objects.filter(
                project=self.instance.project_name
            ).order_by('title')
        
        # 部名
        self.fields['section'].queryset = Section.objects.filter(is_active=True)
        self.fields['section'].empty_label = "部署を選択してください"

        # MUB担当者
        self.fields['mub_manager'].queryset = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['mub_manager'].empty_label = "MUB担当者を選択（任意）"

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 工数の自動計算を実行
        if self.cleaned_data.get('auto_calculate_workdays', False):
            workdays_data = instance.calculate_workdays_from_workload()
            instance.used_workdays = workdays_data['used_workdays']
            instance.newbie_workdays = workdays_data['newbie_workdays']
        
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        
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
        
        return cleaned_data

# フィルターフォームも更新
class WorkloadAggregationFilterForm(forms.Form):
    """工数集計フィルターフォーム（ProjectTicket対応版）"""
    
    project_name = forms.ModelChoiceField(
        label='プロジェクト名',
        queryset=Project.objects.filter(is_active=True),
        required=False,
        empty_label="全てのプロジェクト",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    case_name = forms.ModelChoiceField(
        label='案件名',
        queryset=ProjectTicket.objects.select_related('project'),
        required=False,
        empty_label="全てのチケット",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    section = forms.ModelChoiceField(
        label='課名',
        queryset=Section.objects.filter(is_active=True),
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
        queryset=User.objects.filter(is_active=True),
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