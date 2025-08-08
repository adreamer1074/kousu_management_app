from django import forms
from django.contrib.auth import get_user_model
from datetime import date
from .models import BusinessPartner, OutsourcingCost
from apps.projects.models import Project, ProjectTicket

User = get_user_model()

class BusinessPartnerForm(forms.ModelForm):
    """ビジネスパートナー登録フォーム"""
    
    class Meta:
        model = BusinessPartner
        fields = [
            'name', 'email', 'phone', 'company',
            'hourly_rate', 'projects', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '氏名を入力してください'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '090-1234-5678'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '所属会社名'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '100',
                'placeholder': '5000'
            }),
            'projects': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'multiple': True,
                'size': '8'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '備考があれば入力してください'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # プロジェクトの選択肢を設定
        self.fields['projects'].queryset = Project.objects.filter(
            is_active=True
        ).order_by('name')
        
        # 必須フィールドの設定
        self.fields['name'].required = True
        self.fields['hourly_rate'].required = True
        
        # ヘルプテキスト設定
        self.fields['hourly_rate'].help_text = '時間単価を円単位で入力してください'
        self.fields['projects'].help_text = 'このBPが参加可能なプロジェクトを選択（複数選択可）'


class OutsourcingCostForm(forms.ModelForm):
    """外注費登録フォーム"""
    
    class Meta:
        model = OutsourcingCost
        fields = [
            'year_month', 'business_partner', 'project', 'ticket',
            'status', 'case_classification', 'work_hours', 'notes'
        ]
        widgets = {
            'year_month': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2024-01',
                'pattern': r'\d{4}-\d{2}'
            }),
            'business_partner': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_business_partner'
            }),
            'project': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_project'
            }),
            'ticket': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_ticket'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'case_classification': forms.Select(attrs={
                'class': 'form-select'
            }),
            'work_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.1',
                'placeholder': '8.0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '備考があれば入力してください'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 初期値設定
        if not self.instance.pk:
            # 新規作成時のデフォルト年月
            current_date = date.today()
            self.fields['year_month'].initial = current_date.strftime('%Y-%m')
        
        # ビジネスパートナーの選択肢
        self.fields['business_partner'].queryset = BusinessPartner.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['business_partner'].empty_label = "ビジネスパートナーを選択"
        
        # プロジェクトの選択肢
        self.fields['project'].queryset = Project.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['project'].empty_label = "プロジェクトを選択"
        
        # チケットの選択肢（初期は空）
        if self.instance.pk and self.instance.project:
            # 編集時：選択されたプロジェクトのチケットのみ表示
            self.fields['ticket'].queryset = ProjectTicket.objects.filter(
                project=self.instance.project,
                is_active=True
            ).order_by('title')
        elif 'project' in self.data:
            # フォーム送信時：選択されたプロジェクトのチケットのみ表示
            try:
                project_id = int(self.data.get('project'))
                self.fields['ticket'].queryset = ProjectTicket.objects.filter(
                    project_id=project_id,
                    is_active=True
                ).order_by('title')
            except (ValueError, TypeError):
                self.fields['ticket'].queryset = ProjectTicket.objects.none()
        else:
            # 新規作成時：プロジェクト未選択のため空
            self.fields['ticket'].queryset = ProjectTicket.objects.none()
        
        self.fields['ticket'].empty_label = "チケットを選択"
        
        # 必須フィールドの設定
        self.fields['year_month'].required = True
        self.fields['business_partner'].required = True
        self.fields['project'].required = True
        self.fields['ticket'].required = True
        self.fields['work_hours'].required = True
        
        # ヘルプテキスト設定
        self.fields['year_month'].help_text = 'YYYY-MM形式で入力（例：2024-01）'
        self.fields['work_hours'].help_text = '作業時間を時間単位で入力（例：8.0）'
    
    def clean_year_month(self):
        """年月の形式チェック"""
        year_month = self.cleaned_data.get('year_month')
        if year_month:
            import re
            if not re.match(r'^\d{4}-\d{2}$', year_month):
                raise forms.ValidationError('YYYY-MM形式で入力してください（例：2024-01）')
            
            # 年月の妥当性チェック
            try:
                year, month = map(int, year_month.split('-'))
                if month < 1 or month > 12:
                    raise forms.ValidationError('月は01〜12の範囲で入力してください')
            except ValueError:
                raise forms.ValidationError('正しい年月を入力してください')
        
        return year_month
    
    def clean(self):
        """フォーム全体のバリデーション"""
        cleaned_data = super().clean()
        
        # プロジェクトとチケットの整合性チェック
        project = cleaned_data.get('project')
        ticket = cleaned_data.get('ticket')
        
        if project and ticket:
            if ticket.project != project:
                self.add_error('ticket', '選択されたチケットは選択されたプロジェクトに属していません。')
        
        # ビジネスパートナーとプロジェクトの参加チェック
        business_partner = cleaned_data.get('business_partner')
        project = cleaned_data.get('project')
        
        if business_partner and project:
            if project not in business_partner.projects.all():
                self.add_error('project', 'このビジネスパートナーは選択されたプロジェクトに参加していません。')
        
        return cleaned_data


class OutsourcingCostFilterForm(forms.Form):
    """外注費フィルターフォーム"""
    
    year_month = forms.CharField(
        label='年月',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '2024-01'
        })
    )
    business_partner = forms.ModelChoiceField(
        label='ビジネスパートナー',
        queryset=BusinessPartner.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="全てのBP",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    project = forms.ModelChoiceField(
        label='プロジェクト',
        queryset=Project.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="全てのプロジェクト",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label='ステータス',
        choices=[('', '全てのステータス')] + OutsourcingCost.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    case_classification = forms.ChoiceField(
        label='チケット分類',
        choices=[('', '全てのチケット分類')] + OutsourcingCost.CASE_CLASSIFICATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )