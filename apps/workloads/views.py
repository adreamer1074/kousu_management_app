from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
import json
import calendar

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

@login_required
@require_http_methods(["POST"])
def create_workload_ajax(request):
    """AJAX工数行追加"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        ticket_id = data.get('ticket_id')  # オプション
        year_month = data.get('year_month')
        
        # 必須項目のチェック
        if not user_id:
            return JsonResponse({'success': False, 'error': '担当者を選択してください'})
        
        if not year_month:
            return JsonResponse({'success': False, 'error': '年月を指定してください'})
        
        user = get_object_or_404(User, id=user_id)
        
        # チケットが指定されている場合
        if ticket_id:
            ticket = get_object_or_404(ProjectTicket, id=ticket_id)
            project = ticket.project
        else:
            # チケットが指定されていない場合は、デフォルトプロジェクトまたはエラー
            # ここでは簡単なダミープロジェクトを作成するか、既存のプロジェクトを使用
            project = None
            ticket = None
            # プロジェクトがない場合のデフォルト処理
            default_project = Project.objects.filter(is_active=True).first()
            if default_project:
                project = default_project
            else:
                return JsonResponse({'success': False, 'error': 'プロジェクトまたはチケットを選択してください'})
        
        # 権限チェック
        user_section = getattr(user, 'section', None)
        request_user_section = getattr(request.user, 'section', None)
        user_department = getattr(user, 'department', None)
        request_user_department = getattr(request.user, 'department', None)
        
        if not (request.user.is_staff or request.user.is_superuser or 
                user == request.user or
                (request_user_section and user_section == request_user_section) or
                (request_user_department and user_department == request_user_department)):
            return JsonResponse({'success': False, 'error': '権限がありません'})
        
        # 重複チェック
        existing_workload = Workload.objects.filter(
            user=user,
            project=project,
            ticket=ticket,
            year_month=year_month
        ).first()
        
        if existing_workload:
            return JsonResponse({'success': False, 'error': 'この組み合わせの工数行は既に存在します'})
        
        # 工数行作成
        workload = Workload.objects.create(
            user=user,
            project=project,
            ticket=ticket,
            year_month=year_month
        )
        
        return JsonResponse({'success': True, 'workload_id': workload.id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def update_workload_ajax(request):
    """AJAX工数更新"""
    try:
        data = json.loads(request.body)
        workload_id = data.get('workload_id')
        day = data.get('day')
        value = data.get('value', 0)
        
        workload = get_object_or_404(Workload, id=workload_id)
        
        # 権限チェック
        user_section = getattr(request.user, 'section', None)
        workload_user_section = getattr(workload.user, 'section', None)
        user_department = getattr(request.user, 'department', None)
        workload_user_department = getattr(workload.user, 'department', None)
        
        if not (request.user.is_staff or request.user.is_superuser or 
                workload.user == request.user or
                (user_section and workload_user_section == user_section) or
                (user_department and workload_user_department == user_department)):
            return JsonResponse({'success': False, 'error': '権限がありません'})
        
        # 工数更新
        try:
            value = float(value) if value else 0
            if value < 0 or value > 24:
                return JsonResponse({'success': False, 'error': '工数は0-24の範囲で入力してください'})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': '正しい数値を入力してください'})
        
        # 日付の妥当性チェック
        try:
            day = int(day)
            if day < 1 or day > 31:
                return JsonResponse({'success': False, 'error': '正しい日付を入力してください'})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': '正しい日付を入力してください'})
        
        workload.set_day_value(day, value)
        workload.save()
        
        return JsonResponse({
            'success': True, 
            'total_hours': float(workload.total_hours),
            'total_days': float(workload.total_days)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def delete_workload_ajax(request):
    """AJAX工数行削除"""
    try:
        data = json.loads(request.body)
        workload_id = data.get('workload_id')
        
        if not workload_id:
            return JsonResponse({'success': False, 'error': '工数IDが指定されていません'})
        
        workload = get_object_or_404(Workload, id=workload_id)
        
        # 権限チェック
        user_section = getattr(request.user, 'section', None)
        workload_user_section = getattr(workload.user, 'section', None)
        user_department = getattr(request.user, 'department', None)
        workload_user_department = getattr(workload.user, 'department', None)
        
        if not (request.user.is_staff or request.user.is_superuser or 
                workload.user == request.user or
                (user_section and workload_user_section == user_section) or
                (user_department and workload_user_department == user_department)):
            return JsonResponse({'success': False, 'error': '削除権限がありません'})
        
        # 削除実行
        workload_info = {
            'user': workload.user.get_full_name() or workload.user.username,
            'project': workload.project.name,
            'ticket': workload.ticket.title if workload.ticket else 'なし'
        }
        
        workload.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f"{workload_info['user']}の{workload_info['ticket']}の工数行を削除しました"
        })
        
    except Exception as e:
        import traceback
        print(f"Error in delete_workload_ajax: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})