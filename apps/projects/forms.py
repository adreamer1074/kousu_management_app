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
            'project_no', 'name', 'description', 'client', 
            'start_date', 'end_date', 'budget', 
            'assigned_section', 'assigned_users'
        ]
        widgets = {
            'project_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '',
            }),
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

    def clean_project_no(self):
        """プロジェクト番号のバリデーション"""
        project_no = self.cleaned_data.get('project_no')
        
        if project_no:
            # 重複チェック（編集時は自分自身を除外）
            queryset = Project.objects.filter(project_no=project_no)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError('このプロジェクト番号は既に使用されています。')
        
        return project_no
    
class ProjectTicketForm(forms.ModelForm):
    """プロジェクトチケットフォーム"""
    
    class Meta:
        model = ProjectTicket
        fields = [
            'ticket_no', 'project', 'title', 'description', 
            'priority', 'status', 'case_classification', 'billing_status',
            'assigned_user', 'due_date', 'is_active'
        ]
        # フォームのウィジェット設定(見た目や振る舞い設定)
        widgets = {
            'ticket_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: TICKET-001, TASK-2024-001'
            }),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'case_classification': forms.Select(attrs={'class': 'form-select'}),
            'billing_status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_user': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        # プロジェクトの初期値を取得
        initial_project = kwargs.get('initial', {}).get('project')
        super().__init__(*args, **kwargs)
        
        # プロジェクトのクエリセットを有効なもののみに絞る
        self.fields['project'].queryset = Project.objects.filter(is_active=True).order_by('name')
        
        # 担当者を有効なユーザーのみに絞る
        try:
            from apps.users.models import CustomUser
            self.fields['assigned_user'].queryset = CustomUser.objects.filter(is_active=True).order_by('last_name', 'first_name')
        except:
            pass
        
        # 必須フィールドの設定
        self.fields['title'].required = True
        self.fields['project'].required = True
        self.fields['case_classification'].required = True
        self.fields['status'].required = True
        
        # チケット番号のヘルプテキスト
        self.fields['ticket_no'].help_text = (
            '任意でチケット番号を設定できます。空白でも構いません。'
        )
        
        # プロジェクトが指定されている場合、選択肢から隠す
        if initial_project:
            self.fields['project'].widget = forms.HiddenInput()
            self.fields['project'].initial = initial_project
    
    def clean_ticket_no(self):
        """チケット番号のバリデーション"""
        ticket_no = self.cleaned_data.get('ticket_no')
        
        if ticket_no:
            # 重複チェック（編集時は自分自身を除外）
            queryset = ProjectTicket.objects.filter(ticket_no=ticket_no)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError('このチケット番号は既に使用されています。')
        
        return ticket_no