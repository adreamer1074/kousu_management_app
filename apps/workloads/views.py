from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib import messages
import json
import calendar
from decimal import Decimal

from .models import Workload
from apps.projects.models import Project, ProjectTicket
from apps.users.models import Department

User = get_user_model()

class WorkloadCalendarView(LoginRequiredMixin, TemplateView):
    """工数カレンダー表示"""
    template_name = 'workloads/workload_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 年月の取得（デフォルトは現在月）
        year_month = self.request.GET.get('year_month', timezone.now().strftime('%Y-%m'))
        department_filter = self.request.GET.get('department', '')
        section_filter = self.request.GET.get('section', '')
        
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

        # selectで関連データを取得（ticketとprojectの両方）
        workloads = workloads.select_related(
            'user', 'project', 'ticket', 'user__section', 'user__department'
        ).order_by(
            'user__department__name', 'user__section__name', 'user__username', 'project__name', 'ticket__title'
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
        
        # 全チケット一覧（プロジェクトごとに整理）
        tickets = ProjectTicket.objects.select_related('project').filter(
            project__is_active=True
        ).order_by('project__name', 'title')

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
            'departments': departments,
            'sections': sections,
            'projects': projects,
            'tickets': tickets,  # チケット一覧を追加
            'all_users': all_users,
            'selected_department': department_filter,
            'selected_section': section_filter,
            'is_admin': user.is_staff or user.is_superuser,
            'unique_users_count': unique_users,
            'year_month_first_day': first_day.weekday(),
        })
        
        return context

class WorkloadListView(LoginRequiredMixin, ListView):
    """工数一覧ビュー"""
    model = Workload
    template_name = 'workloads/workload_list.html'
    context_object_name = 'workloads'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Workload.objects.select_related(
                'user', 'project', 'ticket'
            ).order_by('-year_month', 'user__username')
        else:
            return Workload.objects.filter(user=user).select_related(
                'project', 'ticket'
            ).order_by('-year_month')

class WorkloadCreateView(LoginRequiredMixin, CreateView):
    """工数作成ビュー"""
    model = Workload
    template_name = 'workloads/workload_form.html'
    fields = ['user', 'project', 'ticket', 'year_month']
    success_url = reverse_lazy('workloads:workload_calendar')

    def form_valid(self, form):
        messages.success(self.request, '工数を作成しました。')
        return super().form_valid(form)

class WorkloadDetailView(LoginRequiredMixin, DetailView):
    """工数詳細ビュー"""
    model = Workload
    template_name = 'workloads/workload_detail.html'
    context_object_name = 'workload'

class WorkloadUpdateView(LoginRequiredMixin, UpdateView):
    """工数編集ビュー"""
    model = Workload
    template_name = 'workloads/workload_form.html'
    fields = ['user', 'project', 'ticket', 'year_month']
    success_url = reverse_lazy('workloads:workload_calendar')

    def form_valid(self, form):
        messages.success(self.request, '工数を更新しました。')
        return super().form_valid(form)

class WorkloadDeleteView(LoginRequiredMixin, DeleteView):
    """工数削除ビュー"""
    model = Workload
    template_name = 'workloads/workload_delete.html'
    success_url = reverse_lazy('workloads:workload_calendar')

    def delete(self, request, *args, **kwargs):
        messages.success(request, '工数を削除しました。')
        return super().delete(request, *args, **kwargs)

@login_required
@require_http_methods(["POST"])
def create_workload_ajax(request):
    """新規工数行作成AJAX"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        project_id = data.get('project_id')
        ticket_id = data.get('ticket_id')
        year_month = data.get('year_month')
        
        # バリデーション
        if not all([user_id, project_id, ticket_id, year_month]):
            return JsonResponse({
                'success': False,
                'error': '必須項目が不足しています。'
            })
        
        from django.contrib.auth import get_user_model
        from apps.projects.models import Project, ProjectTicket
        
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            project = Project.objects.get(id=project_id)
            ticket = ProjectTicket.objects.get(id=ticket_id)
        except (User.DoesNotExist, Project.DoesNotExist, ProjectTicket.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '指定されたユーザー、プロジェクト、またはチケットが見つかりません。'
            })
        
        # 重複チェック
        existing_workload = Workload.objects.filter(
            user=user,
            project=project,
            ticket=ticket,
            year_month=year_month
        ).first()
        
        if existing_workload:
            return JsonResponse({
                'success': False,
                'error': 'この組み合わせの工数行は既に存在します。'
            })
        
        # 新規工数行を作成
        workload = Workload.objects.create(
            user=user,
            project=project,
            ticket=ticket,
            year_month=year_month
        )
        
        return JsonResponse({
            'success': True,
            'workload_id': workload.id,
            'message': '新しい工数行を作成しました。'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'サーバーエラー: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def update_workload_ajax(request):
    """工数更新AJAX"""
    try:
        data = json.loads(request.body)
        workload_id = data.get('workload_id')
        day = data.get('day')
        value = data.get('value', 0)
        
        # バリデーション
        if not workload_id or not day:
            return JsonResponse({
                'success': False,
                'error': '必須パラメータが不足しています。'
            })
        
        try:
            workload = Workload.objects.get(id=workload_id)
        except Workload.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '指定された工数データが見つかりません。'
            })
        
        # 権限チェック（本人または管理者のみ）
        if workload.user != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': '編集権限がありません。'
            })
        
        # 値の範囲チェック
        try:
            value = float(value) if value else 0.0
            if value < 0 or value > 24:
                return JsonResponse({
                    'success': False,
                    'error': '工数は0-24の範囲で入力してください。'
                })
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': '無効な値です。'
            })
        
        # 工数を更新
        workload.set_day_value(day, value)
        workload.save()
        
        return JsonResponse({
            'success': True,
            'total_hours': workload.total_hours,
            'total_days': workload.total_days,
            'message': f'{day}日の工数を更新しました。'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'サーバーエラー: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def bulk_update_workload_ajax(request):
    """一括工数更新AJAX"""
    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])
        
        if not changes:
            return JsonResponse({
                'success': False,
                'error': '更新する項目がありません。'
            })
        
        updated_count = 0
        errors = []
        
        for change in changes:
            workload_id = change.get('workload_id')
            day = change.get('day')
            value = change.get('value', 0)
            
            try:
                workload = Workload.objects.get(id=workload_id)
                
                # 権限チェック
                if workload.user != request.user and not request.user.is_staff:
                    errors.append(f'工数ID {workload_id}: 編集権限がありません')
                    continue
                
                # 値の範囲チェック
                value = float(value) if value else 0.0
                if value < 0 or value > 24:
                    errors.append(f'工数ID {workload_id}, {day}日: 値が範囲外です')
                    continue
                
                # 工数を更新
                workload.set_day_value(day, value)
                workload.save()
                updated_count += 1
                
            except Workload.DoesNotExist:
                errors.append(f'工数ID {workload_id}: データが見つかりません')
                continue
            except (ValueError, TypeError):
                errors.append(f'工数ID {workload_id}, {day}日: 無効な値です')
                continue
            except Exception as e:
                errors.append(f'工数ID {workload_id}: {str(e)}')
                continue
        
        if updated_count > 0:
            return JsonResponse({
                'success': True,
                'updated_count': updated_count,
                'errors': errors,
                'message': f'{updated_count}件の工数を更新しました。'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': '更新に失敗しました。',
                'errors': errors
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'サーバーエラー: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def delete_workload_ajax(request):
    """工数行削除AJAX"""
    try:
        data = json.loads(request.body)
        workload_id = data.get('workload_id')
        
        if not workload_id:
            return JsonResponse({
                'success': False,
                'error': '工数IDが指定されていません。'
            })
        
        try:
            workload = Workload.objects.get(id=workload_id)
        except Workload.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '指定された工数データが見つかりません。'
            })
        
        # 権限チェック（本人または管理者のみ）
        if workload.user != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': '削除権限がありません。'
            })
        
        # 工数行を削除
        workload_info = f"{workload.user.get_full_name()} - {workload.ticket.title if workload.ticket else workload.project.name}"
        workload.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'工数行を削除しました: {workload_info}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'サーバーエラー: {str(e)}'
        })