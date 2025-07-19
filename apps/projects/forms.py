from django import forms
from django.contrib.auth import get_user_model
from .models import Project, ProjectMember, ProjectPhase, ProjectStatus, ProjectPriority

User = get_user_model()

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name', 'code', 'description', 'client', 'status', 'priority',
            'start_date', 'end_date', 'budget', 'estimated_hours',
            'manager', 'department', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'プロジェクト名を入力'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PROJ-2025-001'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'プロジェクトの説明を入力'
            }),
            'client': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'クライアント名を入力'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(
            is_staff=True, is_active=True
        )
        self.fields['manager'].empty_label = "-- マネージャーを選択 --"
        self.fields['manager'].required = False

class ProjectMemberForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        fields = ['user', 'role', 'hourly_rate', 'join_date', 'leave_date', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 開発者、テスター、デザイナー'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '時間単価（円）'
            }),
            'join_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'leave_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['leave_date'].required = False

class ProjectPhaseForm(forms.ModelForm):
    class Meta:
        model = ProjectPhase
        fields = ['name', 'description', 'start_date', 'end_date', 'estimated_hours', 'order', 'is_completed']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'フェーズ名を入力'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'フェーズの説明を入力'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '順序'
            }),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }