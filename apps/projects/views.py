from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Project, ProjectTicket
from .forms import ProjectForm, ProjectTicketForm

User = get_user_model()

class ProjectListView(LoginRequiredMixin, ListView):
    """プロジェクト一覧"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Project.objects.select_related('assigned_section', 'assigned_section__department').filter(is_active=True)
        
        # 検索フィルター
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(client__icontains=search) |
                Q(description__icontains=search)
            )
        
        # ステータスフィルター
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        # 担当課フィルター
        assigned_section = self.request.GET.get('assigned_section', '')
        if assigned_section:
            queryset = queryset.filter(assigned_section_id=assigned_section)
        
        return queryset.order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # フィルター用のデータ
        context['status_choices'] = Project.STATUS_CHOICES
        
        from apps.users.models import Section
        context['sections'] = Section.objects.filter(is_active=True).select_related('department').order_by('department__name', 'name')
        
        # 現在のフィルター値
        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_assigned_section'] = self.request.GET.get('assigned_section', '')
        
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    """プロジェクト詳細"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tickets'] = self.object.tickets.all().order_by('-created_at')
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    """プロジェクト作成"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'プロジェクトを作成しました。')
        return super().form_valid(form)

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    """プロジェクト編集"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'プロジェクトを更新しました。')
        return super().form_valid(form)

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    """プロジェクト削除"""
    model = Project
    template_name = 'projects/project_delete.html'
    success_url = reverse_lazy('projects:project_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'プロジェクトを削除しました。')
        return super().delete(request, *args, **kwargs)

class ProjectTicketCreateView(LoginRequiredMixin, CreateView):
    """プロジェクトチケット作成"""
    model = ProjectTicket
    form_class = ProjectTicketForm
    template_name = 'projects/ticket_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return kwargs
    
    def form_valid(self, form):
        form.instance.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        messages.success(self.request, 'チケットを作成しました。')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.kwargs['project_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return context

@require_http_methods(["GET"])
def get_project_tickets_api(request, project_id):
    """プロジェクトのチケット一覧を取得するAPI"""
    try:
        project = get_object_or_404(Project, id=project_id, is_active=True)  # プロジェクトのis_activeをチェック
        tickets = project.tickets.all().order_by('-created_at')  # チケットにはis_activeがないので削除
        
        tickets_data = []
        for ticket in tickets:
            tickets_data.append({
                'id': ticket.id,
                'title': ticket.title,
                'status': ticket.status,
                'status_display': ticket.get_status_display(),
                'priority': ticket.priority,
                'priority_display': ticket.get_priority_display(),
            })
        
        return JsonResponse({
            'success': True,
            'tickets': tickets_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })