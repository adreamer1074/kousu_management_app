from django import forms
from django.contrib.auth import get_user_model
from .models import Project, ProjectTicket
from apps.users.models import Department, Section

User = get_user_model()

class ProjectForm(forms.ModelForm):
    """プロジェクトフォーム"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'client', 'status', 
            'start_date', 'end_date', 'budget', 
            'assigned_section', 'assigned_users'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'プロジェクト名を入力してください'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'プロジェクトの詳細説明を入力してください'
            }),
            'client': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'クライアント名を入力してください'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
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
                'step': '0.01'
            }),
            'assigned_section': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_users': forms.SelectMultiple(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 担当課の選択肢を設定
        self.fields['assigned_section'].queryset = Section.objects.filter(
            is_active=True
        ).select_related('department').order_by('department__name', 'name')
        self.fields['assigned_section'].empty_label = "担当課を選択してください"
        
        # 担当者の選択肢を設定
        self.fields['assigned_users'].queryset = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')

class ProjectTicketForm(forms.ModelForm):
    """プロジェクトチケットフォーム"""
    
    class Meta:
        model = ProjectTicket
        fields = [
            'title', 'description', 'case_classification', 'priority', 
            'status', 'billing_status', 'assigned_user', 'due_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'チケットのタイトルを入力してください'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'チケットの詳細説明を入力してください'
            }),
            'case_classification': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'billing_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # 担当者の選択肢を設定
        self.fields['assigned_user'].queryset = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['assigned_user'].empty_label = "担当者を選択してください"
        
        # 必須フィールドのマーク
        required_fields = ['title', 'case_classification', 'status']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # フィールドのヘルプテキストを設定
        self.fields['case_classification'].help_text = 'チケットの分類を選択してください'
        self.fields['priority'].help_text = 'チケットの優先度を設定してください'
        self.fields['status'].help_text = 'チケットの現在のステータスを選択してください'
        self.fields['billing_status'].help_text = '請求に関するステータスを選択してください'
        self.fields['due_date'].help_text = '完了予定日を設定してください'
        
        # プロジェクト情報があれば初期値を設定
        if project:
            self.project = project