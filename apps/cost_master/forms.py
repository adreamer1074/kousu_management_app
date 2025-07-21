from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import CostMaster, ClientBillingRate, ProjectCostSetting
from apps.users.models import Department

class CostMasterForm(forms.ModelForm):
    """コストマスターフォーム"""
    
    class Meta:
        model = CostMaster
        fields = [
            'department', 'employee_level', 'billing_type',
            'monthly_cost', 'monthly_billing',
            'daily_cost', 'daily_billing', 
            'hourly_cost', 'hourly_billing',
            'fixed_cost', 'fixed_billing',
            'overtime_rate', 'holiday_rate',
            'effective_from', 'effective_to', 'is_active'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'employee_level': forms.Select(attrs={'class': 'form-select'}),
            'billing_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_billing_type'}),
            'monthly_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'monthly_billing': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'daily_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'daily_billing': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hourly_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'hourly_billing': forms.NumberInput(attrs={'class': 'form-control'}),
            'fixed_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fixed_billing': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'overtime_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'holiday_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 部署の選択肢を有効なもののみに限定
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        
        # 必須フィールドにマーク追加
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['required'] = True
                if hasattr(field.widget.attrs, 'class'):
                    field.widget.attrs['class'] += ' required'
    
    def clean(self):
        cleaned_data = super().clean()
        effective_from = cleaned_data.get('effective_from')
        effective_to = cleaned_data.get('effective_to')
        billing_type = cleaned_data.get('billing_type')
        
        # 有効期間チェック
        if effective_from and effective_to:
            if effective_to <= effective_from:
                raise ValidationError('有効終了日は有効開始日より後である必要があります。')
        
        # 請求タイプに応じた必須項目チェック
        if billing_type == 'monthly':
            if not cleaned_data.get('monthly_billing'):
                raise ValidationError('月額請求単価は必須です。')
        elif billing_type == 'daily':
            if not cleaned_data.get('daily_billing'):
                raise ValidationError('日額請求単価は必須です。')
        elif billing_type == 'hourly':
            if not cleaned_data.get('hourly_billing'):
                raise ValidationError('時間請求単価は必須です。')
        elif billing_type == 'fixed':
            if not cleaned_data.get('fixed_billing'):
                raise ValidationError('固定請求料金は必須です。')
        
        return cleaned_data
    
    def clean_effective_from(self):
        effective_from = self.cleaned_data.get('effective_from')
        if effective_from and effective_from < date.today():
            # 編集時は過去日付も許可
            if not self.instance.pk:
                raise ValidationError('有効開始日は今日以降である必要があります。')
        return effective_from

class ClientBillingRateForm(forms.ModelForm):
    """取引先別請求単価フォーム"""
    
    class Meta:
        model = ClientBillingRate
        fields = [
            'client_name', 'department', 'employee_level', 'billing_type',
            'monthly_billing', 'daily_billing', 'hourly_billing', 'fixed_billing',
            'discount_rate', 'minimum_billing_amount', 'contract_type', 
            'payment_terms', 'effective_from', 'effective_to', 'is_active'
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '取引先名を入力してください',
                'list': 'client_names'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': '部署を選択（任意）'
            }),
            'employee_level': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'レベルを選択（任意）'
            }),
            'billing_type': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'タイプを選択（任意）'
            }),
            'monthly_billing': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'daily_billing': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'hourly_billing': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0',
                'placeholder': '0'
            }),
            'fixed_billing': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'discount_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '100',
                'placeholder': '0.0'
            }),
            'minimum_billing_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例：月末締め翌月末払い'
            }),
            'effective_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'effective_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 必須フィールドを「取引先名」のみに設定
        for field_name, field in self.fields.items():
            if field_name != 'client_name':
                field.required = False
        
        # 空の選択肢を追加
        self.fields['department'].empty_label = "選択してください（任意）"
        self.fields['employee_level'].empty_label = "選択してください（任意）"
        self.fields['billing_type'].empty_label = "選択してください（任意）"
        
        # デフォルト値設定
        if not self.instance.pk:  # 新規作成時のみ
            from datetime import date
            self.fields['is_active'].initial = True
            self.fields['effective_from'].initial = date.today()
            self.fields['discount_rate'].initial = 0
            self.fields['minimum_billing_amount'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        billing_type = cleaned_data.get('billing_type')
        
        # 請求タイプが選択されている場合のみ、対応する単価をチェック
        if billing_type:
            if billing_type == 'monthly' and not cleaned_data.get('monthly_billing'):
                raise forms.ValidationError('月額請求タイプの場合、月額請求単価は必須です。')
            elif billing_type == 'daily' and not cleaned_data.get('daily_billing'):
                raise forms.ValidationError('日額請求タイプの場合、日額請求単価は必須です。')
            elif billing_type == 'hourly' and not cleaned_data.get('hourly_billing'):
                raise forms.ValidationError('時間請求タイプの場合、時間請求単価は必須です。')
            elif billing_type == 'fixed' and not cleaned_data.get('fixed_billing'):
                raise forms.ValidationError('固定請求タイプの場合、固定請求料金は必須です。')
        
        # 有効期間の整合性チェック
        effective_from = cleaned_data.get('effective_from')
        effective_to = cleaned_data.get('effective_to')
        
        if effective_from and effective_to and effective_from >= effective_to:
            raise forms.ValidationError('有効終了日は有効開始日より後の日付を設定してください。')
        
        return cleaned_data

class ProjectCostSettingForm(forms.ModelForm):
    """案件別コスト設定フォーム"""
    
    class Meta:
        model = ProjectCostSetting
        fields = [
            'project_detail', 'use_client_specific_rate', 'client_billing_rate',
            'custom_monthly_billing', 'custom_daily_billing', 'custom_hourly_billing',
            'setup_cost', 'maintenance_cost',
            'billing_cycle', 'invoice_timing', 'cost_notes'
        ]
        widgets = {
            'project_detail': forms.Select(attrs={'class': 'form-select'}),
            'use_client_specific_rate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'client_billing_rate': forms.Select(attrs={'class': 'form-select'}),
            'custom_monthly_billing': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'custom_daily_billing': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'custom_hourly_billing': forms.NumberInput(attrs={'class': 'form-control'}),
            'setup_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'maintenance_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-select'}),
            'invoice_timing': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }