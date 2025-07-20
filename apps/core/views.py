from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime
from apps.users.models import CustomUser, Department
from apps.projects.models import Project, ProjectTicket
from apps.workloads.models import Workload

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 現在の年月を取得
        current_date = timezone.now()
        current_year = current_date.year
        current_month = current_date.month
        year_month = f"{current_year}-{current_month:02d}"
        
        # 基本統計
        stats = {
            'total_departments': Department.objects.count(),
            'total_projects': Project.objects.filter(is_active=True).count(),
        }
        
        # 今月の工数合計を計算
        if self.request.user.is_staff or self.request.user.is_superuser:
            # 管理者は全ユーザーの工数を表示
            current_month_workloads = Workload.objects.filter(year_month=year_month)
        else:
            # 一般ユーザーは自分の工数のみ
            current_month_workloads = Workload.objects.filter(
                year_month=year_month,
                user=self.request.user
            )
        
        # 今月の合計工数時間を計算
        total_hours_this_month = sum(w.total_hours for w in current_month_workloads)
        stats['current_month_hours'] = total_hours_this_month
        
        # 今月の総チケット数を計算（工数入力で使用されているチケット）
        # 重複を除いてユニークなチケット数をカウント
        if self.request.user.is_staff or self.request.user.is_superuser:
            # 管理者は全チケットを対象
            current_month_tickets = Workload.objects.filter(
                year_month=year_month,
                ticket__isnull=False  # チケットが設定されている工数のみ
            ).values('ticket').distinct().count()
        else:
            # 一般ユーザーは自分の工数のチケットのみ
            current_month_tickets = Workload.objects.filter(
                year_month=year_month,
                user=self.request.user,
                ticket__isnull=False
            ).values('ticket').distinct().count()
        
        stats['current_month_tickets'] = current_month_tickets
        
        # 最近のプロジェクト
        if self.request.user.is_staff or self.request.user.is_superuser:
            recent_projects = Project.objects.filter(is_active=True).order_by('-created_at')[:5]
        else:
            # 一般ユーザーは関連するプロジェクトのみ
            recent_projects = Project.objects.filter(
                is_active=True,
                workload__user=self.request.user
            ).distinct().order_by('-created_at')[:5]
        
        context.update({
            'stats': stats,
            'recent_projects': recent_projects,
            'current_month': current_month,
            'current_year': current_year,
        })
        
        return context

# 関数ベースのビューの場合
@login_required
def home_view(request):
    """ホームページビュー"""
    current_date = timezone.now()
    current_year = current_date.year
    current_month = current_date.month
    year_month = f"{current_year}-{current_month:02d}"
    
    # 基本統計
    stats = {
        'total_departments': Department.objects.count(),
        'total_projects': Project.objects.filter(is_active=True).count(),
    }
    
    # 今月の工数合計を計算
    if request.user.is_staff or request.user.is_superuser:
        # 管理者は全ユーザーの工数を表示
        current_month_workloads = Workload.objects.filter(year_month=year_month)
    else:
        # 一般ユーザーは自分の工数のみ
        current_month_workloads = Workload.objects.filter(
            year_month=year_month,
            user=request.user
        )
    
    # 今月の合計工数時間を計算
    total_hours_this_month = sum(w.total_hours for w in current_month_workloads)
    stats['current_month_hours'] = total_hours_this_month
    
    # 今月の総チケット数を計算（工数入力で使用されているチケット）
    if request.user.is_staff or request.user.is_superuser:
        # 管理者は全チケットを対象
        current_month_tickets = Workload.objects.filter(
            year_month=year_month,
            ticket__isnull=False  # チケットが設定されている工数のみ
        ).values('ticket').distinct().count()
    else:
        # 一般ユーザーは自分の工数のチケットのみ
        current_month_tickets = Workload.objects.filter(
            year_month=year_month,
            user=request.user,
            ticket__isnull=False
        ).values('ticket').distinct().count()
    
    stats['current_month_tickets'] = current_month_tickets
    
    # 最近のプロジェクト
    if request.user.is_staff or request.user.is_superuser:
        recent_projects = Project.objects.filter(is_active=True).order_by('-created_at')[:5]
    else:
        # 一般ユーザーは関連するプロジェクトのみ
        recent_projects = Project.objects.filter(
            is_active=True,
            workload__user=request.user
        ).distinct().order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_projects': recent_projects,
        'current_month': current_month,
        'current_year': current_year,
    }
    
    return render(request, 'core/home.html', context)