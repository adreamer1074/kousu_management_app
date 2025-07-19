from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count
from apps.users.models import CustomUser, Department
from apps.projects.models import Project

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'

    def dispatch(self, request, *args, **kwargs):
        """ユーザー権限に応じてリダイレクト"""
        user = request.user
        
        # 一般ユーザー（スタッフでもスーパーユーザーでもない）は工数入力画面へ
        if user.is_authenticated and not user.is_staff and not user.is_superuser:
            return redirect('workloads:workload_list')
        
        # スタッフ・管理者はダッシュボードを表示
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 基本統計
        context['stats'] = {
            'total_users': CustomUser.objects.filter(is_active=True).count(),
            'total_departments': Department.objects.filter(is_active=True).count(),
            'total_projects': Project.objects.filter(is_active=True).count(),
        }
        
        # 最近のプロジェクト（5件）
        context['recent_projects'] = Project.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5]
        
        return context