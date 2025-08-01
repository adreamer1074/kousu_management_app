from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import date, datetime, timedelta
from apps.users.models import CustomUser
from apps.projects.models import Project,ProjectTicket
from apps.workloads.models import Workload
from apps.reports.models import WorkloadAggregation

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
        
        # === 追加統計情報の計算 ===
        now = timezone.now()
        first_day_of_month = now.replace(day=1)
        
        # 総工数登録数
        workload_count = Workload.objects.count()
        
        # 進行中チケット数
        active_tickets_count = WorkloadAggregation.objects.filter(
            status__in=['planning', 'in_progress'],
            case_name__isnull=False
        ).count()
        
        # 期限超過チケット数
        overdue_tickets_count = WorkloadAggregation.objects.filter(
            planned_end_date__lt=now.date(),
            status__in=['planning', 'in_progress'],
            case_name__isnull=False
        ).count()
        
        # 収益統計
        revenue_stats = WorkloadAggregation.objects.aggregate(
            total_billing=Sum('billing_amount_excluding_tax'),
            total_outsourcing=Sum('outsourcing_cost_excluding_tax')
        )
        
        total_billing = revenue_stats['total_billing'] or 0
        total_outsourcing = revenue_stats['total_outsourcing'] or 0
        
        total_revenue = total_billing
        total_outsourcing_cost = total_outsourcing
        gross_profit = total_revenue - total_outsourcing_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # チケットステータス別統計
        ticket_records = WorkloadAggregation.objects.filter(case_name__isnull=False)
        status_data = ticket_records.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('billing_amount_excluding_tax')*10000  
        ).order_by('-total_amount')
        
        ticket_status_stats = []
        status_colors = {
            'planning': 'secondary',
            'in_progress': 'primary',
            'testing': 'info',
            'completed': 'success',
            'on_hold': 'warning',
            'cancelled': 'danger'
        }
        
        status_display_names = {
            'planning': '企画中',
            'in_progress': '進行中',
            'testing': 'テスト中',
            'completed': '完了',
            'on_hold': '保留',
            'cancelled': 'キャンセル'
        }
        
        for item in status_data:
            status_value = item['status']
            count = item['count']
            amount = item['total_amount'] or 0
            
            display_name = status_display_names.get(status_value, status_value)
            
            ticket_status_stats.append({
                'name': display_name,
                'count': count,
                'total_amount': amount / 10000,  # 万円単位
                'color': status_colors.get(status_value, 'secondary')
            })
        
        # 今月の工数統計
        this_month_stats = WorkloadAggregation.objects.filter(
            created_at__gte=first_day_of_month
        ).aggregate(
            total_workdays=Sum('used_workdays')
        )
        
        this_month_workdays = this_month_stats['total_workdays'] or 0
        
        # 営業日数計算
        working_days_this_month = 0
        current_date = first_day_of_month.date()
        while current_date <= now.date():
            if current_date.weekday() < 5:  # 平日のみ
                working_days_this_month += 1
            current_date += timedelta(days=1)
        
        avg_daily_workdays = this_month_workdays / working_days_this_month if working_days_this_month > 0 else 0
        
        # 前月比較
        last_month_first_day = (first_day_of_month - timedelta(days=1)).replace(day=1)
        last_month_last_day = first_day_of_month - timedelta(days=1)
        
        last_month_stats = WorkloadAggregation.objects.filter(
            created_at__gte=last_month_first_day,
            created_at__lte=last_month_last_day
        ).aggregate(
            total_workdays=Sum('used_workdays')
        )
        
        last_month_workdays = last_month_stats['total_workdays'] or 0
        workdays_growth = ((this_month_workdays - last_month_workdays) / last_month_workdays * 100) if last_month_workdays > 0 else 0
        
        # 目標達成率
        monthly_target = working_days_this_month * 0.8
        target_achievement = (this_month_workdays / monthly_target * 100) if monthly_target > 0 else 0
        
        # 最近の登録データ取得
        recent_workload_entries = []
        recent_aggregations = WorkloadAggregation.objects.select_related(
            'case_name'
        ).order_by('-created_at')[:5]
        
        for aggregation in recent_aggregations:
            recent_workload_entries.append({
                'project_name': aggregation.project_name or '未設定',
                'case_name': {
                    'title': aggregation.case_name.title if aggregation.case_name else '未設定'
                },
                'used_workdays': aggregation.used_workdays or 0,
                'created_at': aggregation.created_at
            })
        
        # 注意チケット取得
        attention_tickets = []
        
        # 期限超過チケット
        overdue_tickets = WorkloadAggregation.objects.filter(
            planned_end_date__lt=now.date(),
            status__in=['planning', 'in_progress'],
            case_name__isnull=False
        ).select_related('case_name')[:3]
        
        for ticket in overdue_tickets:
            days_overdue = (now.date() - ticket.planned_end_date).days
            attention_tickets.append({
                'ticket_title': ticket.case_name.title if ticket.case_name else '未設定',
                'project_name': ticket.project_name,
                'reason': f'予定終了日を{days_overdue}日超過',
                'alert_level': 'danger',
                'status_display': status_display_names.get(ticket.status, ticket.status),
                'days_overdue': days_overdue
            })
        
        # コンテキストに追加
        context.update({
            'title': '管理者ダッシュボード',
            'current_month': now.strftime('%Y年%m月'),
            # 基本統計
            'total_users': total_users,
            'active_users': active_users,
            'staff_users': staff_users,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'total_workload_entries': workload_count,
            'active_tickets_count': active_tickets_count,
            'overdue_tickets_count': overdue_tickets_count,
            # 収益サマリー
            'total_revenue': total_revenue,
            'total_outsourcing_cost': total_outsourcing_cost,
            'gross_profit': gross_profit,
            'profit_margin': profit_margin,
            # 工数統計
            'this_month_workdays': this_month_workdays,
            'avg_daily_workdays': avg_daily_workdays,
            'workdays_growth': workdays_growth,
            'target_achievement': target_achievement,
            # チケット統計
            'ticket_status_stats': ticket_status_stats,
            # 最近の活動
            'recent_workload_entries': recent_workload_entries,
            'attention_tickets': attention_tickets,
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