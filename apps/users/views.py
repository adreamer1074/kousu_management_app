from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser

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
    login_url = '/users/login/'

class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    login_url = '/users/login/'

class UserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user'
    login_url = '/users/login/'

class UserEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'users/user_edit.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'department']
    success_url = reverse_lazy('users:user_list')
    login_url = '/users/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'ユーザー情報が更新されました。')
        return super().form_valid(form)