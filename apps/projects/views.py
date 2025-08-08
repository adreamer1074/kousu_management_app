from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from datetime import date
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from apps.core.decorators import (
    leader_or_superuser_required_403,
    LeaderOrSuperuserRequiredMixin
)
from .models import Project, ProjectTicket
from .forms import ProjectForm, ProjectTicketForm

User = get_user_model()

class ProjectListView(LeaderOrSuperuserRequiredMixin, ListView):
    """プロジェクト一覧"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Project.objects.filter(is_active=True).select_related('assigned_section', 'assigned_section__department')
        
        # 検索フィルター
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(client__icontains=search) |
                Q(description__icontains=search)
            )
        
        
        # 担当課フィルター
        assigned_section = self.request.GET.get('assigned_section', '')
        if assigned_section:
            queryset = queryset.filter(assigned_section_id=assigned_section)
        
        return queryset.order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # フィルター用のデータ
        # context['status_choices'] = Project.STATUS_CHOICES
        
        from apps.users.models import Section
        context['sections'] = Section.objects.filter(is_active=True).select_related('department').order_by('department__name', 'name')
        
        # 現在のフィルター値
        context['current_search'] = self.request.GET.get('search', '')
        # context['current_status'] = self.request.GET.get('status', '')
        context['current_assigned_section'] = self.request.GET.get('assigned_section', '')
        
        return context

class ProjectDetailView(LeaderOrSuperuserRequiredMixin, DetailView):
    """プロジェクト詳細ビュー"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # プロジェクトに関連するチケット一覧を取得
        tickets = self.object.tickets.select_related('assigned_user').order_by('-created_at')
        tickets = self.object.tickets.filter(
            is_active=True
        ).select_related('assigned_user').order_by('-created_at')
        
        context['tickets'] = tickets
        
        # 今日の日付を追加（期限の色分け用）
        context['today'] = date.today()
        
        # チケット統計を計算
        total_tickets = tickets.count()
        closed_tickets = tickets.filter(status='closed').count()
        
        # 進捗率を計算
        progress_percent = 0
        if total_tickets > 0:
            progress_percent = round((closed_tickets / total_tickets) * 100, 1)
        
        context.update({
            'total_tickets': total_tickets,
            'closed_tickets': closed_tickets,
            'in_progress_tickets': tickets.filter(status='in_progress').count(),
            'open_tickets': tickets.filter(status='open').count(),
            'progress_percent': progress_percent,
        })
        
        return context

class ProjectCreateView(LeaderOrSuperuserRequiredMixin, CreateView):
    """プロジェクト作成"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'プロジェクトを作成しました。')
        return super().form_valid(form)

class ProjectUpdateView(LeaderOrSuperuserRequiredMixin, UpdateView):
    """プロジェクト編集"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'プロジェクトを更新しました。')
        return super().form_valid(form)

class ProjectDeleteView(LeaderOrSuperuserRequiredMixin, DeleteView):
    """プロジェクト削除"""
    model = Project
    template_name = 'projects/project_delete.html'
    context_object_name = 'object'
    success_url = reverse_lazy('projects:project_list')

    def get_queryset(self):
        return Project.objects.all()
    
    def post(self, request, *args, **kwargs):
        """POSTリクエストでの削除処理"""     
        return self.delete(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """論理削除を実行"""
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # 削除前の情報を保存
        project_name = self.object.name
        ticket_count = self.object.tickets.filter(is_active=True).count()
        
        # 論理削除実行
        self.object.soft_delete()
        # 成功メッセージ
        if ticket_count > 0:
            messages.success(
                request, 
                f'プロジェクト「{project_name}」と関連チケット{ticket_count}件を削除しました。'
            )
        else:
            messages.success(
                request, 
                f'プロジェクト「{project_name}」を削除しました。'
            )
        
        return HttpResponseRedirect(success_url)
  

class TicketListView(LeaderOrSuperuserRequiredMixin, ListView):
    """チケット一覧ビュー（プロジェクト別・全体対応）"""
    model = ProjectTicket
    template_name = 'projects/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20
    
    def get_queryset(self):
        all_tickets = ProjectTicket.objects.all()
        print(f"全チケット数: {all_tickets.count()}")
        for ticket in all_tickets:
            print(f"チケット: {ticket.pk} - {ticket.title} - プロジェクト: {ticket.project.pk if ticket.project else 'なし'}")
            # print(f"チケット: {ticket.pk} - {ticket.title} - プロジェクト: {ticket.project.pk if ticket.project else 'なし'} - アクティブ: {ticket.is_active}")
        
        queryset = ProjectTicket.objects.select_related(
            'project', 'assigned_user', 'project__assigned_section'
        )
        queryset = ProjectTicket.objects.select_related(
            'project', 'assigned_user', 'project__assigned_section'
        ).filter(is_active=True)
        
        print(f"全チケット数: {queryset.count()}")
        # print(f"アクティブチケット数: {queryset.count()}")
        
        # プロジェクト別フィルター（URLパラメータから）
        project_pk = self.kwargs.get('project_pk')
        print(f"project_pk: {project_pk}")
        
        if project_pk:
            queryset = queryset.filter(project_id=project_pk)
            print(f"プロジェクト{project_pk}のチケット数: {queryset.count()}")
        
        # 検索フィルター
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(ticket_no__icontains=search)
            )
            print(f"検索後のチケット数: {queryset.count()}")
        
        # ステータスフィルター
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
            print(f"ステータス「{status}」フィルター後: {queryset.count()}")
        
        # 優先度フィルター
        priority = self.request.GET.get('priority', '').strip()
        if priority:
            queryset = queryset.filter(priority=priority)
            print(f"優先度「{priority}」フィルター後: {queryset.count()}")
        
        # プロジェクトフィルター（全チケット一覧でのフィルター）
        project_filter = self.request.GET.get('project', '').strip()
        if project_filter and not project_pk:
            try:
                project_id = int(project_filter)
                queryset = queryset.filter(project_id=project_id)
                print(f"プロジェクトフィルター「{project_id}」後: {queryset.count()}")
            except (ValueError, TypeError):
                print(f"無効なプロジェクトID: {project_filter}")
                pass
        
        final_queryset = queryset.order_by('-created_at')
        print(f"最終チケット数: {final_queryset.count()}")
        
        return final_queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # プロジェクト情報（project_pk がある場合）
        project_pk = self.kwargs.get('project_pk')
        if project_pk:
            try:
                context['project'] = get_object_or_404(Project, pk=project_pk)
                print(f"プロジェクト情報取得: {context['project'].name}")
            except Project.DoesNotExist:
                print(f"プロジェクトが見つかりません: {project_pk}")
        
        # 全プロジェクト（フィルター用）
        context['all_projects'] = Project.objects.filter(is_active=True).order_by('name')
        
        # 統計情報
        tickets = self.get_queryset().filter(is_active=True)
        context['total_tickets'] = tickets.count()
        
        # 今日の日付（期限判定用）
        from datetime import date
        context['today'] = date.today()
        
        # 現在のフィルター状態をコンテキストに追加
        context['current_filters'] = {
            'project': self.request.GET.get('project', ''),
            'status': self.request.GET.get('status', ''),
            'priority': self.request.GET.get('priority', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        print(f"コンテキスト - 総チケット数: {context['total_tickets']}")
        
        return context

class TicketDetailView(LeaderOrSuperuserRequiredMixin, DetailView):
    """チケット詳細ビュー"""
    model = ProjectTicket
    template_name = 'projects/ticket_detail.html'
    context_object_name = 'ticket'
    
    def get_queryset(self):
        return ProjectTicket.objects.select_related(
            'project', 'assigned_user', 'project__assigned_section'
        ).prefetch_related(
            'project__assigned_users'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.object
        
        # プロジェクト情報
        context['project'] = ticket.project
        
        # 同じプロジェクトの他のチケット（最新5件）
        context['related_tickets'] = ProjectTicket.objects.filter(
            project=ticket.project,
            is_active=True
        ).exclude(pk=ticket.pk).order_by('-created_at')[:5]
        # 編集権限チェック
        context['can_edit'] = self.request.user.is_superuser or \
                            self.request.user.is_leader or \
                            ticket.assigned_user == self.request.user
        
        # 今日の日付
        from datetime import date
        context['today'] = date.today()
        
        return context

class TicketUpdateView(LeaderOrSuperuserRequiredMixin, UserPassesTestMixin, UpdateView):
    """チケット編集ビュー"""
    model = ProjectTicket
    form_class = ProjectTicketForm
    template_name = 'projects/ticket_form.html'
    context_object_name = 'ticket'
    
    def test_func(self):
        """編集権限チェック"""
        ticket = self.get_object()
        return (
            self.request.user.is_superuser or 
            self.request.user.is_leader or 
            ticket.assigned_user == self.request.user
        )
    
    def handle_no_permission(self):
        """権限がない場合の処理"""
        messages.error(self.request, 'このチケットを編集する権限がありません。')
        return redirect('projects:ticket_detail', pk=self.get_object().pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context
    
    def form_valid(self, form):
        """フォーム送信成功時の処理"""
        # 更新者のみを設定（作成者は変更しない）
        form.instance.updated_by = self.request.user
        
        messages.success(self.request, f'チケット「{form.instance.title}」を更新しました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """フォーム送信失敗時の処理"""
        messages.error(self.request, 'チケットの更新に失敗しました。入力内容を確認してください。')
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('projects:ticket_detail', kwargs={'pk': self.object.pk})

class TicketDeleteView(LeaderOrSuperuserRequiredMixin, UserPassesTestMixin, DeleteView):
    """チケット削除ビュー"""
    model = ProjectTicket
    template_name = 'projects/ticket_delete.html'
    context_object_name = 'ticket'
    success_url = reverse_lazy('projects:ticket_list')
    
    def get_queryset(self):
        # アクティブなチケットのみを対象
        return ProjectTicket.objects.filter(is_active=True).select_related(
            'project', 'assigned_user', 'project__assigned_section'
        )
    
    def get_success_url(self):
        """削除後は該当プロジェクトの詳細ページに戻る"""
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})
    
    def handle_no_permission(self):
        """権限がない場合の処理"""
        messages.error(self.request, 'このチケットを削除する権限がありません。')
        return redirect('projects:ticket_detail', pk=self.get_object().pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context
    
    def post(self, request, *args, **kwargs):
        """POSTリクエストでの削除処理"""     
        return self.delete(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """論理削除を実行"""
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # 削除前の情報を保存
        ticket_title = self.object.title
        
        # 論理削除実行
        self.object.soft_delete()
        
        # 成功メッセージ
        messages.success(
            request, 
            f'チケット「{ticket_title}」を削除しました。'
        )
        
        return HttpResponseRedirect(success_url)



class ProjectTicketCreateView(LeaderOrSuperuserRequiredMixin, UserPassesTestMixin, CreateView):
    """チケット作成ビュー"""
    model = ProjectTicket
    form_class = ProjectTicketForm
    template_name = 'projects/ticket_form.html'
    
    def test_func(self):
        """作成権限チェック"""
        return (
            self.request.user.is_superuser or 
            self.request.user.is_leader or 
            self.request.user.is_active
        )
    
    def get_initial(self):
        """初期値設定"""
        initial = super().get_initial()
        initial['is_active'] = True
        project_pk = self.kwargs.get('project_pk')
        print(f"チケット作成 - project_pk: {project_pk}")

        
        if project_pk:
            try:
                project = get_object_or_404(Project, pk=project_pk)
                initial['project'] = project
                print(f"プロジェクト設定: {project.name} (ID: {project.pk})")
            except Project.DoesNotExist:
                print(f"プロジェクトが見つかりません: {project_pk}")
        
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs.get('project_pk')
        if project_pk:
            try:
                context['project'] = get_object_or_404(Project, pk=project_pk)
                print(f"コンテキストにプロジェクト設定: {context['project'].name}")
            except Project.DoesNotExist:
                print(f"コンテキスト用プロジェクトが見つかりません: {project_pk}")
        return context
    
    def form_valid(self, form):
        """フォーム送信成功時の処理"""
        # 作成者・更新者を設定
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        # プロジェクトが設定されているかチェック
        if not form.instance.project:
            project_pk = self.kwargs.get('project_pk')
            if project_pk:
                try:
                    form.instance.project = get_object_or_404(Project, pk=project_pk)
                    print(f"フォーム送信時にプロジェクト設定: {form.instance.project.name}")
                except Project.DoesNotExist:
                    print(f"フォーム送信時プロジェクトが見つかりません: {project_pk}")
                    messages.error(self.request, 'プロジェクトが見つかりません。')
                    return self.form_invalid(form)
        
        print(f"保存前チケット情報:")
        print(f"  - タイトル: {form.instance.title}")
        print(f"  - プロジェクト: {form.instance.project}")
        # print(f"  - is_active: {form.instance.is_active}")
        print(f"  - created_by: {form.instance.created_by}")
        
        result = super().form_valid(form)
        
        print(f"保存後チケット情報:")
        print(f"  - ID: {form.instance.pk}")
        print(f"  - タイトル: {form.instance.title}")
        print(f"  - プロジェクト: {form.instance.project}")
        # print(f"  - is_active: {form.instance.is_active}")
        
        messages.success(self.request, f'チケット「{form.instance.title}」を作成しました。')
        return result
    
    def form_invalid(self, form):
        """フォーム送信失敗時の処理"""
        print("フォームが無効です:")
        for field, errors in form.errors.items():
            print(f"  - {field}: {errors}")
        
        messages.error(self.request, 'チケットの作成に失敗しました。入力内容を確認してください。')
        return super().form_invalid(form)
    
    def get_success_url(self):
        # プロジェクト別チケット一覧に戻る
        project_pk = self.kwargs.get('project_pk')
        if project_pk:
            return reverse('projects:project_ticket_list', kwargs={'project_pk': project_pk})
        else:
            return reverse('projects:ticket_detail', kwargs={'pk': self.object.pk})

@login_required
@require_http_methods(["GET"])
def get_project_tickets_api(request, project_id):
    """プロジェクトのチケット一覧API"""
    try:
        project = get_object_or_404(Project, pk=project_id)
        # tickets = ProjectTicket.objects.filter(
            # project=project
        # ).select_related('assigned_user')
        tickets = ProjectTicket.objects.filter(
            project=project,
            is_active=True
        ).select_related('assigned_user')
        
        tickets_data = []
        for ticket in tickets:
            tickets_data.append({
                'id': ticket.pk,
                'ticket_no': ticket.ticket_no or '',
                'title': ticket.title,
                'status': ticket.status,
                'status_display': ticket.get_status_display(),
                'priority': ticket.priority,
                'priority_display': ticket.get_priority_display(),
                'assigned_user': ticket.assigned_user.get_full_name() if ticket.assigned_user else '',
                'due_date': ticket.due_date.isoformat() if ticket.due_date else None,
                'created_at': ticket.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'tickets': tickets_data,
            'total': len(tickets_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@leader_or_superuser_required_403
@require_http_methods(["GET"])
def get_tickets_api(request):
    """全チケット一覧API"""
    try:
        tickets = ProjectTicket.objects.filter(
            is_active=True
        ).select_related('project', 'assigned_user')
        
        # フィルター適用 - パラメータ名を統一
        project_id = request.GET.get('project_id')  # ← ここを修正：'project' から 'project_id' に変更
        if project_id:
            tickets = tickets.filter(project_id=project_id)
            print(f"プロジェクトID {project_id} でフィルタリング: {tickets.count()}件")  # デバッグ用
        
        status = request.GET.get('status')
        if status:
            tickets = tickets.filter(status=status)
        
        priority = request.GET.get('priority')
        if priority:
            tickets = tickets.filter(priority=priority)
        
        tickets_data = []
        for ticket in tickets:
            tickets_data.append({
                'id': ticket.pk,
                'ticket_no': ticket.ticket_no or '',
                'title': ticket.title,
                'project_id': ticket.project.pk,
                'project_name': ticket.project.name,
                'status': ticket.status,
                'status_display': ticket.get_status_display(),
                'priority': ticket.priority,
                'priority_display': ticket.get_priority_display(),
                'assigned_user': ticket.assigned_user.get_full_name() if ticket.assigned_user else '',
                'due_date': ticket.due_date.isoformat() if ticket.due_date else None,
                'created_at': ticket.created_at.isoformat(),
                # 工数集計フォーム用のフィールドを追加
                'case_classification': getattr(ticket, 'case_classification', ''),
            })
        
        print(f"最終的に返すチケット数: {len(tickets_data)}件")  # デバッグ用
        
        return JsonResponse({
            'success': True,
            'tickets': tickets_data,
            'total': len(tickets_data)
        })
        
    except Exception as e:
        print(f"チケット取得API エラー: {str(e)}")  # デバッグ用
        return JsonResponse({
            'success': False,
            'error': str(e)
        })