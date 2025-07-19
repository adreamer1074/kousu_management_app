from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from .models import CustomUser, Department, Section
from .forms import UserEditForm, ProfileEditForm, DepartmentForm, SectionForm

def register(request):
    """ユーザー登録ビュー"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'アカウント「{username}」が作成されました。')
            login(request, user)
            return redirect('core:home')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

# ユーザー管理ビュー
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/user/profile.html"  # 修正
    login_url = '/login/'

class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/user/user_list.html'  # 修正
    context_object_name = 'users'
    paginate_by = 20
    login_url = '/login/'

class UserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/user/user_detail.html'  # 修正
    context_object_name = 'user'
    login_url = '/login/'

class UserEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'users/user/user_edit.html'  # 修正
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

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = 'users/user/profile_edit.html'  # 修正
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
    template_name = 'users/department/department_list.html'  # 修正
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
    template_name = 'users/department/department_detail.html'  # 修正
    context_object_name = 'department'
    login_url = '/login/'

class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'users/department/department_form.html'  # 修正
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
    template_name = 'users/department/department_form.html'  # 修正
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
    template_name = 'users/department/department_confirm_delete.html'  # 修正
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

# 課管理ビュー
class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = 'users/section/section_list.html'  # 修正
    context_object_name = 'sections'
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """管理者権限チェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '課管理には管理者権限が必要です。')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True)
        return context

class SectionDetailView(LoginRequiredMixin, DetailView):
    model = Section
    template_name = 'users/section/section_detail.html'  # 修正
    context_object_name = 'section'
    login_url = '/login/'

class SectionCreateView(LoginRequiredMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'users/section/section_form.html'  # 修正
    success_url = reverse_lazy('users:section_list')
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        """管理者権限チェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '課作成には管理者権限が必要です。')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'課「{form.instance.full_name}」を作成しました。')
        return super().form_valid(form)

class SectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'users/section/section_form.html'  # 修正
    success_url = reverse_lazy('users:section_list')
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """管理者権限チェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '課編集には管理者権限が必要です。')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'課「{form.instance.full_name}」を更新しました。')
        return super().form_valid(form)

class SectionDeleteView(LoginRequiredMixin, DeleteView):
    model = Section
    template_name = 'users/section/section_confirm_delete.html'  # 修正
    success_url = reverse_lazy('users:section_list')
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """管理者権限チェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '課削除には管理者権限が必要です。')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        section_name = self.get_object().full_name
        messages.success(request, f'課「{section_name}」を削除しました。')
        return super().delete(request, *args, **kwargs)

# AJAX用ビュー
@login_required
def load_sections(request):
    """部署選択時に課をロードするAJAXビュー"""
    department_id = request.GET.get('department_id')
    sections = Section.objects.filter(
        department_id=department_id, 
        is_active=True
    ).order_by('name')
    
    section_list = [{'id': '', 'name': '-- 課を選択 --'}]
    section_list.extend([
        {'id': section.id, 'name': section.name} 
        for section in sections
    ])
    
    return JsonResponse({'sections': section_list})