from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib import messages
from apps.users.models import CustomUser, Department
from apps.projects.models import Project, ProjectTicket
from apps.workloads.models import Workload
from datetime import datetime, date

class CustomLoginView(LoginView):
    """ユーザー権限別リダイレクト機能付きログインビュー"""
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        user = self.request.user
        
        # ログイン成功メッセージ
        messages.success(self.request, f'ようこそ、{user.username}さん！')
        
        if user.is_superuser:
            # スーパーユーザー → 管理ダッシュボード
            return reverse('core:admin_dashboard')
        elif user.is_staff:
            # スタッフ → スタッフダッシュボード
            return reverse('core:staff_dashboard')
        else:
            # 一般ユーザー → 個人ダッシュボード
            return reverse('core:user_dashboard')

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """スーパーユーザー専用ダッシュボード"""
    template_name = 'dashboard/admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'アクセス権限がありません。')
        return redirect('core:user_dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # システム統計情報
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        staff_users = CustomUser.objects.filter(is_staff=True).count()
        
        try:
            total_projects = Project.objects.count()
            active_projects = Project.objects.filter(is_active=True).count()
        except:
            total_projects = 0
            active_projects = 0
        
        context.update({
            'title': '管理ダッシュボード',
            'total_users': total_users,
            'active_users': active_users,
            'staff_users': staff_users,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'pending_reports': 0,  # TODO: 実装予定
            'system_alerts': [],   # TODO: 実装予定
        })
        return context

class StaffDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """スタッフ専用ダッシュボード"""
    template_name = 'dashboard/staff_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, 'アクセス権限がありません。')
        return redirect('core:user_dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # スタッフが管理する情報
        context.update({
            'title': 'スタッフダッシュボード',
            'managed_users': CustomUser.objects.filter(department=user.department, is_active=True).exclude(id=user.id),
            'my_projects': user.project_set.filter(is_active=True) if hasattr(user, 'project_set') else [],
        })
        return context

class UserDashboardView(LoginRequiredMixin, TemplateView):
    """一般ユーザー専用ダッシュボード"""
    template_name = 'dashboard/user_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 今日の日付
        today = date.today()
        this_month_start = today.replace(day=1)
        
        # ユーザーの基本情報
        context.update({
            'title': 'ダッシュボード',
            'user': user,
            'today': today,
            'today_workload_exists': False,  # TODO: 工数アプリ実装後に修正
            'my_projects': [],  # TODO: プロジェクト参加情報
            'recent_workloads': [],  # TODO: 最近の工数履歴
            'this_month_hours': 0,   # TODO: 今月の合計工数
            'this_week_hours': 0,    # TODO: 今週の合計工数
            'pending_tasks': [],     # TODO: 未完了タスク
        })
        return context

# 既存のHomeViewをそのまま保持
class HomeView(LoginRequiredMixin, TemplateView):
    """ホーム画面（リダイレクト用）"""
    template_name = 'dashboard/home.html'
    
    def dispatch(self, request, *args, **kwargs):
        """ログイン後は適切なダッシュボードにリダイレクト"""
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect('core:admin_dashboard')
            elif request.user.is_staff:
                return redirect('core:staff_dashboard')
            else:
                return redirect('core:user_dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'ホーム'
        return context