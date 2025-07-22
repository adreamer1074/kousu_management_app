from django import forms
from datetime import date
from .models import CostMaster
from apps.users.models import Department, CustomUser

class CostMasterForm(forms.ModelForm):
    """コストマスターフォーム"""
    
    class Meta:
        model = CostMaster
        fields = [
            'client_name', 'billing_type', 'department', 'manager', 'employee_level',
            'monthly_billing', 'daily_billing', 'hourly_billing', 'fixed_billing',
            'discount_rate', 'minimum_billing_amount', 'special_conditions',
            'contract_type', 'payment_terms', 'effective_from', 'effective_to', 'is_active'
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請求先名を入力してください',
            }),
            'billing_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'employee_level': forms.Select(attrs={'class': 'form-select'}),
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
            'special_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '割引条件や特別な取り決めなど'
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
        
        # 空の選択肢を追加
        # self.fields['department'].empty_label = "部署を選択（任意）"
        # self.fields['manager'].empty_label = "責任者を選択（任意）"
        # self.fields['employee_level'].empty_label = "レベルを選択（任意）"
        
        # 責任者の選択肢をアクティブなユーザーに限定
        self.fields['manager'].queryset = CustomUser.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')
        
        # デフォルト値設定
        if not self.instance.pk:  # 新規作成時のみ
            self.fields['is_active'].initial = True
            self.fields['effective_from'].initial = date.today()
            self.fields['discount_rate'].initial = 0
            self.fields['minimum_billing_amount'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        billing_type = cleaned_data.get('billing_type')
        
        # 請求タイプに応じた単価の必須チェック
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
        
        # 割引率の妥当性チェック
        discount_rate = cleaned_data.get('discount_rate', 0)
        if discount_rate < 0 or discount_rate > 100:
            raise forms.ValidationError('割引率は0%から100%の範囲で設定してください。')
        
        return cleaned_data