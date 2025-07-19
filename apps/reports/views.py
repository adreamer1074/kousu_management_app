from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count
from apps.workloads.models import Workload
from apps.projects.models import Project

class ReportListView(LoginRequiredMixin, TemplateView):
    """レポート一覧"""
    template_name = 'reports/report_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 管理者・スタッフは全体統計、一般ユーザーは個人統計
        if user.is_staff or user.is_superuser:
            # 全体統計
            context['total_hours'] = Workload.objects.aggregate(
                total=Sum('hours')
            )['total'] or 0
            
            context['total_projects'] = Project.objects.filter(
                is_active=True
            ).count()
            
            context['is_admin_view'] = True
        else:
            # 個人統計
            context['total_hours'] = Workload.objects.filter(
                user=user
            ).aggregate(total=Sum('hours'))['total'] or 0
            
            context['total_projects'] = Project.objects.filter(
                is_active=True,
                workload__user=user
            ).distinct().count()
            
            context['is_admin_view'] = False
        
        # 共通：ユーザー個人の工数情報
        context['user_workloads'] = Workload.objects.filter(
            user=user
        ).aggregate(
            total=Sum('hours'),
            count=Count('id')
        )
        
        return context