from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import secrets
import string
from .models import CustomUser, Department, Section

class CustomUserCreationForm(forms.ModelForm):
    """管理者用カスタムユーザー作成フォーム"""
    password1 = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='8文字以上で入力してください。',
        required=False
    )
    password2 = forms.CharField(
        label='パスワード（確認）',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='確認のため、同じパスワードを入力してください。',
        required=False
    )
    auto_generate_password = forms.BooleanField(
        label='ランダムパスワード自動生成',
        required=False,
        initial=True
    )
    # 隠しフィールド
    auto_generate_password = forms.BooleanField(
        widget=forms.HiddenInput(),
        required=False,
        initial=True
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'department', 'section', 'employee_level',
                 'is_leader', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select', 'onchange': 'loadSections(this.value)'}),
            'section': forms.Select(attrs={'class': 'form-select', 'id': 'id_section'}),
            'employee_level': forms.Select(attrs={'class': 'form-select'}),
            'is_leader': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['section'].queryset = Section.objects.filter(is_active=True)
        self.fields['department'].empty_label = "選択してください"
        self.fields['section'].empty_label = "選択してください"
        self.fields['employee_level'].empty_label = "選択してください"
        self.fields['is_active'].initial = True

        # 必須フィールド
        self.fields['username'].required = True
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        
    def generate_random_password(self):
        """セキュアなランダムパスワードを生成"""
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        return password

    def clean(self):
        cleaned_data = super().clean()
        auto_generate = self.data.get('auto_generate_password') == 'on'
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        cleaned_data['auto_generate_password'] = auto_generate

        if not auto_generate:
            if not password1:
                raise ValidationError({'password1': 'パスワードを入力してください。'})
            if not password2:
                raise ValidationError({'password2': 'パスワード確認を入力してください。'})
            if password1 != password2:
                raise ValidationError({'password2': 'パスワードが一致しません。'})

            try:
                validate_password(password1)
            except ValidationError as e:
                raise ValidationError({'password1': e.messages})

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # パスワード設定
        auto_generate = self.cleaned_data.get('auto_generate_password', True)
        if auto_generate:
            password = self.generate_random_password()
            self.generated_password = password  # 後で表示用に保存
        else:
            password = self.cleaned_data['password1']

        user.set_password(password)

        if commit:
            user.save()
        return user

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'department', 'section']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'employee_level': forms.Select(attrs={'class': 'form-select'}),
        }

class SuperUserEditForm(forms.ModelForm):
    """スーパーユーザー用完全編集フォーム"""
    password = None  # パスワードフィールドを除外

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'section', 
                 'is_leader', 'is_superuser', 'is_active', 'employee_level']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'is_leader': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'employee_level': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['section'].queryset = Section.objects.filter(is_active=True)
        self.fields['department'].empty_label = "選択してください"
        self.fields['section'].empty_label = "選択してください"
        self.fields['employee_level'].empty_label = "選択してください"

class UserEditForm(forms.ModelForm):
    """一般管理者用ユーザー編集フォーム"""
    password = None  # パスワードフィールドを除外

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'section', 'is_leader', 'is_active', 'employee_level']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'is_leader': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'employee_level': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['section'].queryset = Section.objects.filter(is_active=True)
        self.fields['department'].empty_label = "選択してください"
        self.fields['section'].empty_label = "選択してください"
        self.fields['employee_level'].empty_label = "選択してください"

class ProfileEditForm(forms.ModelForm):
    """一般ユーザー用プロフィール編集フォーム（部署編集不可）"""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class DepartmentForm(forms.ModelForm):
    """部署フォーム"""
    class Meta:
        model = Department
        fields = ['name', 'description', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = CustomUser.objects.filter(is_active=True)
        self.fields['manager'].empty_label = "選択してください"

class SectionForm(forms.ModelForm):
    """課フォーム"""
    class Meta:
        model = Section
        fields = ['name', 'department', 'description', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['manager'].queryset = CustomUser.objects.filter(is_active=True)
        self.fields['department'].empty_label = "選択してください"
        self.fields['manager'].empty_label = "選択してください"

class AdminUserCreationForm(forms.ModelForm):
    """管理者専用ユーザー作成フォーム（自動ログイン完全防止）"""
    password1 = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='8文字以上で入力してください。'
    )
    password2 = forms.CharField(
        label='パスワード（確認）',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='確認のため、同じパスワードを入力してください。'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'department', 'section', 'employee_level',
                 'is_leader', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'employee_level': forms.Select(attrs={'class': 'form-select'}),
            'is_leader': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("パスワードが一致しません。")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
        return user

class WorkloadAggregationForm(forms.ModelForm):
    """業務量集計フォーム"""
    # ...既存のフィールド...

    unit_cost_per_month = forms.DecimalField(
        label='単価（万円/月）',
        max_digits=8,
        decimal_places=1,
        required=False,
        initial=75.0,  # デフォルト値を75に設定
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0',
            'placeholder': '75.0'
        })
    )
    
    billing_unit_cost_per_month = forms.DecimalField(
        label='請求単価（万円/月）',
        max_digits=8,
        decimal_places=1,
        required=False,
        initial=90.0,  # デフォルト値を90に設定
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0',
            'placeholder': '90.0'
        })
    )
    
    # ...既存のコード...