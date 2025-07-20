from django import forms
from django.contrib.auth import get_user_model
from .models import Project, ProjectTicket

User = get_user_model()

class ProjectForm(forms.ModelForm):
    """プロジェクトフォーム"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'client', 'start_date', 'end_date', 
            'budget', 'assigned_section'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'プロジェクト名を入力'
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
                'step': '0.01',
                'placeholder': '予算を入力'
            }),
            'assigned_section': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 課の選択肢を設定
        from apps.users.models import Section
        self.fields['assigned_section'].queryset = Section.objects.filter(is_active=True).order_by('department__name', 'name')
        
        # ラベル設定
        self.fields['name'].label = 'プロジェクト名 *'
        self.fields['description'].label = '説明'
        self.fields['client'].label = 'クライアント'
        self.fields['start_date'].label = '開始日'
        self.fields['end_date'].label = '終了日'
        self.fields['budget'].label = '予算'
        self.fields['assigned_section'].label = '担当課'
        
        # 必須フィールド設定
        self.fields['name'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('開始日は終了日より前に設定してください。')
        
        return cleaned_data

class ProjectTicketForm(forms.ModelForm):
    """プロジェクトチケットフォーム"""
    
    class Meta:
        model = ProjectTicket
        fields = ['title', 'description', 'priority', 'status', 'assigned_user', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'チケットタイトルを入力'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'チケットの説明を入力'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
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
        
        # 担当者の選択肢を設定（プロジェクトの担当課のユーザーに限定）
        if project and project.assigned_section:
            self.fields['assigned_user'].queryset = User.objects.filter(
                section=project.assigned_section,
                is_active=True
            ).order_by('username')
        else:
            self.fields['assigned_user'].queryset = User.objects.filter(is_active=True).order_by('username')
        
        # ラベル設定
        self.fields['title'].label = 'タイトル *'
        self.fields['description'].label = '説明'
        self.fields['priority'].label = '優先度'
        self.fields['status'].label = 'ステータス'
        self.fields['assigned_user'].label = '担当者'
        self.fields['due_date'].label = '期限'
        
        # 必須フィールド設定
        self.fields['title'].required = True