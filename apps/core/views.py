from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import date, datetime, timedelta
from apps.users.models import CustomUser
from apps.projects.models import Project
from apps.workloads.models import Workload

class CustomLoginView(LoginView):
    """ユーザー権限別リダイレクト機能付きログインビュー"""
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        user = self.request.user
        
        # ログイン成功メッセージ
        messages.success(self.request, f'お帰りなさい、{user.username}さん！')
        
        if user.is_superuser:
            # スーパーユーザー → 管理ダッシュボード
            return reverse('core:admin_dashboard')
        elif user.is_staff:
            # リーダー → リーダーダッシュボード
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
    """リーダー専用ダッシュボード"""
    template_name = 'dashboard/staff_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, 'アクセス権限がありません。')
        return redirect('core:user_dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # リーダーが管理する情報
        context.update({
            'title': 'リーダーダッシュボード',
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
        
        # 日付計算
        today = date.today()
        this_month_start = today.replace(day=1)
        current_year_month = today.strftime('%Y-%m')
        
        # 今週の開始日（月曜日）
        today_weekday = today.weekday()  # 0=月曜日, 6=日曜日
        this_week_start = today - timedelta(days=today_weekday)
        
        # 今月の工数を取得
        this_month_workloads = Workload.objects.filter(
            user=user,
            year_month=current_year_month
        )
        
        # 今月の合計工数を計算
        this_month_hours = 0
        for workload in this_month_workloads:
            this_month_hours += workload.total_hours
        
        # 今週の合計工数を計算
        this_week_hours = 0
        for workload in this_month_workloads:
            # 今週の日付範囲内の工数のみ合計
            for day_num in range((today - this_week_start).days + 1):
                target_date = this_week_start + timedelta(days=day_num)
                if target_date.month == today.month and target_date.year == today.year:
                    day_hours = workload.get_day_value(target_date.day)
                    this_week_hours += day_hours
        
        # 参加中のプロジェクト（正しいフィールド名を使用）
        my_projects = Project.objects.filter(
            workloads__user=user,  # workload → workloads に修正
            is_active=True
        ).distinct()
        
        # 最近の工数履歴（直近5件）
        recent_workloads = Workload.objects.filter(
            user=user
        ).select_related('project').order_by('-year_month', '-updated_at')[:5]
        
        # 今日の工数入力状況をチェック
        today_workload_exists = False
        today_workloads = Workload.objects.filter(
            user=user,
            year_month=current_year_month
        )
        
        for workload in today_workloads:
            day_hours = workload.get_day_value(today.day)
            if day_hours > 0:
                today_workload_exists = True
                break
        
        # 未入力日数の計算（今月の平日で工数が0の日をカウント）
        pending_tasks_count = 0
        import calendar
        
        # 今月の日数を取得
        _, last_day = calendar.monthrange(today.year, today.month)
        
        for day in range(1, min(today.day + 1, last_day + 1)):  # 今日まで
            # 平日かどうかチェック
            check_date = date(today.year, today.month, day)
            if check_date.weekday() < 5:  # 月曜日(0)〜金曜日(4)
                # その日の工数合計をチェック
                day_total = 0
                for workload in today_workloads:
                    day_total += workload.get_day_value(day)
                
                if day_total == 0:
                    pending_tasks_count += 1
        
        context.update({
            'title': 'ダッシュボード',
            'user': user,
            'today': today,
            'today_workload_exists': today_workload_exists,
            'my_projects': my_projects,
            'recent_workloads': recent_workloads,
            'this_month_hours': round(this_month_hours, 1),
            'this_week_hours': round(this_week_hours, 1),
            'pending_tasks': {'count': pending_tasks_count},  # countアトリビュート用
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