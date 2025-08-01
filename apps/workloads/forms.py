from django import forms
from .models import Workload
from apps.projects.models import Project

class WorkloadForm(forms.ModelForm):
    """従来の工数入力フォーム（個別入力用）"""
    
    class Meta:
        model = Workload
        fields = ['project', 'year_month', 'total_hours', 'total_days']
        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-select'
            }),
            'year_month': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'month',
                'placeholder': 'YYYY-MM'
            }),
            'total_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0',
                'placeholder': '例: 160'
            }),
            'total_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': '例: 20'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # アクティブなプロジェクトのみを選択肢に表示
        self.fields['project'].queryset = Project.objects.filter(is_active=True)
        self.fields['project'].empty_label = "プロジェクトを選択してください"
        
        # 必須フィールドのラベルに * を追加
        self.fields['project'].label = "プロジェクト *"
        self.fields['year_month'].label = "年月 *"
        self.fields['total_hours'].label = "工数（時間）*"
        self.fields['total_days'].label = "工数（人日）*"

class WorkloadCalendarForm(forms.Form):
    """カレンダー形式工数入力用フォーム"""
    user = forms.ModelChoiceField(
        queryset=None,
        empty_label="担当者を選択",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.filter(is_active=True),
        empty_label="案件を選択",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    year_month = forms.CharField(
        widget=forms.TextInput(attrs={'type': 'month', 'class': 'form-control'})
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            if user.is_leader or user.is_superuser:
                # 管理者は全ユーザーを選択可能
                from apps.users.models import CustomUser
                self.fields['user'].queryset = CustomUser.objects.filter(is_active=True)
            else:
                # 一般ユーザーは自分のみ
                self.fields['user'].queryset = user.__class__.objects.filter(id=user.id)
                self.fields['user'].initial = user
                self.fields['user'].widget.attrs['readonly'] = True