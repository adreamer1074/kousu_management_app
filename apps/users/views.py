from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser
from .forms import UserEditForm, ProfileEditForm

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