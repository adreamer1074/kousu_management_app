from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Department, Section

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'department', 'section']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
        }

class UserEditForm(forms.ModelForm):
    """管理者用ユーザー編集フォーム（部署・課編集可能）"""
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'department', 'section']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'updateSections(this.value)'
            }),
            'section': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].queryset = Section.objects.none()
        
        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['section'].queryset = Section.objects.filter(
                    department_id=department_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['section'].queryset = self.instance.department.sections.filter(
                is_active=True
            ).order_by('name') if self.instance.department else Section.objects.none()

class ProfileEditForm(forms.ModelForm):
    """一般ユーザー用プロフィール編集フォーム（部署・課編集不可）"""
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '部署名を入力'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '部署の説明を入力（任意）'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = CustomUser.objects.filter(
            is_staff=True, is_active=True
        )
        self.fields['manager'].empty_label = "-- マネージャーを選択 --"
        self.fields['manager'].required = False

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'department', 'description', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '課名を入力（例：1課、2課）'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '課の説明を入力（任意）'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = CustomUser.objects.filter(
            is_staff=True, is_active=True
        )
        self.fields['manager'].empty_label = "-- 課長を選択 --"
        self.fields['manager'].required = False