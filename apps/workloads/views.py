from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime
import calendar
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model

from .models import Workload
from .forms import WorkloadForm
from apps.projects.models import Project
from apps.users.models import Department

User = get_user_model()

class WorkloadCalendarView(LoginRequiredMixin, TemplateView):
    """工数入力画面（カレンダー形式）"""
    template_name = 'workloads/workload_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 年月の取得（デフォルトは現在月）
        year_month = self.request.GET.get('year_month', timezone.now().strftime('%Y-%m'))
        department_filter = self.request.GET.get('department', '')  # 部署フィルター
        section_filter = self.request.GET.get('section', '')        # 課フィルター
        
        try:
            year, month = map(int, year_month.split('-'))
        except:
            year, month = timezone.now().year, timezone.now().month
            year_month = f"{year:04d}-{month:02d}"

        # 該当月の日数を取得
        days_in_month = calendar.monthrange(year, month)[1]
        
        # ユーザー権限に応じたクエリセット
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # 管理者は全データを表示
            workloads = Workload.objects.filter(year_month=year_month)
            
            # 部署フィルター
            if department_filter:
                workloads = workloads.filter(user__department_id=department_filter)
            
            # 課フィルター
            if section_filter:
                workloads = workloads.filter(user__section_id=section_filter)
                
            # 管理者は全ユーザーを表示
            all_users = User.objects.filter(is_active=True).order_by('username')
        else:
            # 一般ユーザーは自分の課のみ
            if hasattr(user, 'section') and user.section:
                workloads = Workload.objects.filter(
                    year_month=year_month,
                    user__section=user.section
                )
                # 同じ課のユーザーのみ表示
                all_users = User.objects.filter(
                    is_active=True,
                    section=user.section
                ).order_by('username')
            elif hasattr(user, 'department') and user.department:
                workloads = Workload.objects.filter(
                    year_month=year_month,
                    user__department=user.department
                )
                # 同じ部署のユーザーのみ表示
                all_users = User.objects.filter(
                    is_active=True,
                    department=user.department
                ).order_by('username')
            else:
                workloads = Workload.objects.filter(
                    year_month=year_month,
                    user=user
                )
                # 自分のみ表示
                all_users = User.objects.filter(id=user.id)

        workloads = workloads.select_related('user', 'project', 'user__section', 'user__department').order_by(
            'user__department__name', 'user__section__name', 'user__username', 'project__name'
        )

        # 統計計算
        unique_users = workloads.values('user').distinct().count()

        # 部署一覧（フィルター用）
        if user.is_staff or user.is_superuser:
            departments = Department.objects.filter(is_active=True).order_by('name')
        else:
            user_department = getattr(user, 'department', None)
            if user_department:
                departments = Department.objects.filter(id=user_department.id)
            else:
                departments = Department.objects.none()

        # 課一覧（フィルター用）
        if user.is_staff or user.is_superuser:
            from apps.users.models import Section
            sections = Section.objects.filter(is_active=True).select_related('department').order_by('department__name', 'name')
        else:
            user_section = getattr(user, 'section', None)
            if user_section:
                sections = Section.objects.filter(id=user_section.id)
            else:
                sections = Section.objects.none()

        # アクティブなプロジェクト一覧
        projects = Project.objects.filter(is_active=True).order_by('name')

        # 月の最初の日（曜日計算用）
        from datetime import date
        first_day = date(year, month, 1)

        context.update({
            'year_month': year_month,
            'year': year,
            'month': month,
            'days_in_month': days_in_month,
            'day_range': range(1, days_in_month + 1),
            'workloads': workloads,
            'departments': departments,        # 部署一覧
            'sections': sections,             # 課一覧
            'projects': projects,
            'all_users': all_users,
            'selected_department': department_filter,  # 選択された部署
            'selected_section': section_filter,       # 選択された課
            'is_admin': user.is_staff or user.is_superuser,
            'unique_users_count': unique_users,
            'year_month_first_day': first_day.weekday(),
        })
        
        return context

class WorkloadDetailView(LoginRequiredMixin, DetailView):
    """工数詳細表示"""
    model = Workload
    template_name = 'workloads/workload_detail.html'
    context_object_name = 'workload'

    def get_queryset(self):
        user = self.request.user
        # 管理者・スタッフは全ての工数を表示、一般ユーザーは自分の工数のみ
        if user.is_staff or user.is_superuser:
            return Workload.objects.select_related('user', 'project', 'department')
        else:
            return Workload.objects.filter(user=user).select_related('user', 'project', 'department')

class WorkloadCreateView(LoginRequiredMixin, CreateView):
    """工数入力（従来形式）"""
    model = Workload
    form_class = WorkloadForm
    template_name = 'workloads/workload_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        # 部署情報を自動設定
        user_department = getattr(self.request.user, 'department', None)
        if user_department:
            form.instance.department = user_department
        elif hasattr(self.request.user, 'section') and self.request.user.section and self.request.user.section.department:
            form.instance.department = self.request.user.section.department
        
        messages.success(self.request, '工数を登録しました。')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('workloads:workload_list')

class WorkloadUpdateView(LoginRequiredMixin, UpdateView):
    """工数編集"""
    model = Workload
    form_class = WorkloadForm
    template_name = 'workloads/workload_form.html'
    
    def get_queryset(self):
        user = self.request.user
        # 管理者・スタッフは全ての工数を編集可能、一般ユーザーは自分の工数のみ
        if user.is_staff or user.is_superuser:
            return Workload.objects.all()
        else:
            return Workload.objects.filter(user=user)
    
    def form_valid(self, form):
        messages.success(self.request, '工数を更新しました。')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('workloads:workload_detail', kwargs={'pk': self.object.pk})

class WorkloadDeleteView(LoginRequiredMixin, DeleteView):
    """工数削除"""
    model = Workload
    template_name = 'workloads/workload_delete.html'
    
    def get_queryset(self):
        user = self.request.user
        # 管理者・スタッフは全ての工数を削除可能、一般ユーザーは自分の工数のみ
        if user.is_staff or user.is_superuser:
            return Workload.objects.all()
        else:
            return Workload.objects.filter(user=user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '工数を削除しました。')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('workloads:workload_list')

@require_http_methods(["POST"])
def save_workload_ajax(request):
    """AJAX工数保存"""
    try:
        data = json.loads(request.body)
        workload_id = data.get('workload_id')
        day = data.get('day')
        hours = data.get('hours', 0)
        
        workload = get_object_or_404(Workload, id=workload_id)
        
        # 権限チェック
        user_department = getattr(request.user, 'department', None)
        if not (request.user.is_staff or request.user.is_superuser or 
                workload.user == request.user or 
                (user_department and workload.department == user_department)):
            return JsonResponse({'success': False, 'error': '権限がありません'})
        
        # 日別工数を更新
        workload.set_day_value(day, hours)
        workload.save()
        
        return JsonResponse({
            'success': True,
            'total_hours': str(workload.total_hours),
            'total_days': str(workload.total_days)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
def create_workload_ajax(request):
    """AJAX工数行作成"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        project_id = data.get('project_id')
        year_month = data.get('year_month')
        
        user_obj = get_object_or_404(User, id=user_id)
        project = get_object_or_404(Project, id=project_id)
        
        # 権限チェック
        user_department = getattr(request.user, 'department', None)
        user_obj_department = getattr(user_obj, 'department', None)
        
        if not (request.user.is_staff or request.user.is_superuser or 
                user_obj == request.user or
                (user_department and user_obj_department == user_department)):
            return JsonResponse({'success': False, 'error': '権限がありません'})
        
        # 既存チェック
        if Workload.objects.filter(user=user_obj, project=project, year_month=year_month).exists():
            return JsonResponse({'success': False, 'error': '既に同じ工数行が存在します'})
        
        # 工数行作成
        workload = Workload.objects.create(
            user=user_obj,
            project=project,
            year_month=year_month,
            department=user_obj_department
        )
        
        return JsonResponse({'success': True, 'workload_id': workload.id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# 既存のビューをエイリアス（後方互換性のため）
WorkloadListView = WorkloadCalendarView