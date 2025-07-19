from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser, Department
from .forms import UserEditForm, ProfileEditForm, DepartmentForm 

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'アカウント {username} が作成されました。')
            login(request, user)
            return redirect('core:home')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"
    login_url = '/login/'

class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    login_url = '/login/'

class UserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user'
    login_url = '/login/'

class UserEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'users/user_edit.html'
    success_url = reverse_lazy('users:user_list')
    login_url = '/login/'
    
    def get_form_class(self):
        """権限に応じて適切なフォームを返す"""
        if self.request.user.is_staff or self.request.user.is_superuser:
            return UserEditForm
        else:
            return ProfileEditForm
    
    def dispatch(self, request, *args, **kwargs):
        """権限チェック"""
        # 一般ユーザーが他人のプロフィールを編集しようとした場合
        if not (request.user.is_staff or request.user.is_superuser):
            if self.get_object() != request.user:
                messages.error(request, '他のユーザーの情報は編集できません。')
                return redirect('users:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'ユーザー情報が更新されました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit_department'] = (
            self.request.user.is_staff or self.request.user.is_superuser
        )
        return context

# プロフィール編集専用ビュー（自分のプロフィールのみ）
class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    login_url = '/login/'
    
    def get_object(self):
        """常に現在のユーザーのプロフィールを返す"""
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'プロフィールが更新されました。')
        return super().form_valid(form)

# 部署管理ビュー
class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'users/department_list.html'
    context_object_name = 'departments'
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """管理者権限チェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '部署管理には管理者権限が必要です。')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        departments = context['departments']
        
        # 統計情報を追加
        context['active_departments_count'] = departments.filter(is_active=True).count()
        context['total_users_count'] = sum(dept.user_count for dept in departments)
        context['departments_without_manager'] = departments.filter(manager__isnull=True).count()
        
        return context

class DepartmentDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = 'users/department_detail.html'
    context_object_name = 'department'
    login_url = '/login/'

class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'users/department_form.html'
    success_url = reverse_lazy('users:department_list')
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """管理者権限チェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '部署作成には管理者権限が必要です。')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'部署「{form.instance.name}」を作成しました。')
        return super().form_valid(form)

class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'users/department_form.html'
    success_url = reverse_lazy('users:department_list')
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """管理者権限チェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '部署編集には管理者権限が必要です。')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'部署「{form.instance.name}」を更新しました。')
        return super().form_valid(form)

class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Department
    template_name = 'users/department_confirm_delete.html'
    success_url = reverse_lazy('users:department_list')
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """管理者権限チェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '部署削除には管理者権限が必要です。')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        dept_name = self.get_object().name
        messages.success(request, f'部署「{dept_name}」を削除しました。')
        return super().delete(request, *args, **kwargs)