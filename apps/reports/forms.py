from django import forms
from django.contrib.auth import get_user_model
from datetime import date, datetime
from .models import WorkloadAggregation
from apps.users.models import Department
from apps.projects.models import Project, ProjectDetail

User = get_user_model()

class WorkloadAggregationForm(forms.ModelForm):
    """工数集計フォーム"""
    
    class Meta:
        model = WorkloadAggregation
        fields = [
            'project', 'project_detail', 'year_month', 'budget', 'billing_amount',
            'outsourcing_cost', 'estimated_workdays', 'used_workdays', 'status',
            'progress_rate', 'department', 'manager', 'notes'
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'project_detail': forms.Select(attrs={'class': 'form-select'}),
            'year_month': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2024-12',
                'pattern': '[0-9]{4}-[0-9]{2}'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'billing_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'outsourcing_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'estimated_workdays': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0',
                'placeholder': '0.0'
            }),
            'used_workdays': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0',
                'placeholder': '0.0'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'progress_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': '0'
            }),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '備考があれば記載してください'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # プロジェクトの絞り込み（アクティブなもののみ）
        self.fields['project'].queryset = Project.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['project'].empty_label = "プロジェクトを選択してください"
        
        # プロジェクト詳細の絞り込み
        if self.instance.pk and self.instance.project:
            self.fields['project_detail'].queryset = ProjectDetail.objects.filter(
                project=self.instance.project
            )
        else:
            self.fields['project_detail'].queryset = ProjectDetail.objects.none()
        self.fields['project_detail'].empty_label = "プロジェクト詳細を選択（任意）"
        
        # 部署の絞り込み
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].empty_label = "担当部署を選択（任意）"
        
        # マネージャーの絞り込み
        self.fields['manager'].queryset = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['manager'].empty_label = "プロジェクトマネージャーを選択（任意）"
        
        # デフォルト値設定
        if not self.instance.pk:  # 新規作成時
            current_date = datetime.now()
            self.fields['year_month'].initial = f"{current_date.year}-{current_date.month:02d}"
            self.fields['status'].initial = 'planning'
            self.fields['progress_rate'].initial = 0

    def clean_year_month(self):
        year_month = self.cleaned_data.get('year_month')
        if year_month:
            try:
                # YYYY-MM形式の検証
                year, month = year_month.split('-')
                year = int(year)
                month = int(month)
                if not (1 <= month <= 12):
                    raise ValueError("月は1-12の範囲で入力してください")
                if year < 2000 or year > 2100:
                    raise ValueError("年は2000-2100の範囲で入力してください")
            except ValueError as e:
                raise forms.ValidationError(f"年月の形式が正しくありません: {e}")
        return year_month

    def clean(self):
        cleaned_data = super().clean()
        
        # 進捗率の妥当性チェック
        progress_rate = cleaned_data.get('progress_rate')
        if progress_rate is not None and (progress_rate < 0 or progress_rate > 100):
            raise forms.ValidationError('進捗率は0%から100%の範囲で設定してください。')
        
        # 工数の妥当性チェック
        estimated_workdays = cleaned_data.get('estimated_workdays')
        used_workdays = cleaned_data.get('used_workdays')
        if estimated_workdays and used_workdays:
            if used_workdays > estimated_workdays * 1.5:  # 150%を超える場合は警告
                self.add_error('used_workdays', 
                    '消化工数が見積工数の150%を超えています。確認してください。')
        
        # 予算の妥当性チェック
        budget = cleaned_data.get('budget')
        billing_amount = cleaned_data.get('billing_amount')
        if budget and billing_amount:
            if billing_amount > budget * 1.2:  # 120%を超える場合は警告
                self.add_error('billing_amount', 
                    '請求金額が予算の120%を超えています。確認してください。')
        
        return cleaned_data

class WorkloadAggregationFilterForm(forms.Form):
    """工数集計フィルターフォーム"""
    
    year_month = forms.CharField(
        label='年月',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '2024-12',
            'pattern': '[0-9]{4}-[0-9]{2}'
        })
    )
    project = forms.ModelChoiceField(
        label='プロジェクト',
        queryset=Project.objects.filter(is_active=True),
        required=False,
        empty_label="全てのプロジェクト",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        label='部署',
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="全ての部署",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label='ステータス',
        choices=[('', '全てのステータス')] + WorkloadAggregation.StatusChoices.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    manager = forms.ModelChoiceField(
        label='プロジェクトマネージャー',
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="全てのマネージャー",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        label='検索',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'プロジェクト名で検索'
        })
    )