from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from .models import Project, ProjectMember, ProjectPhase, ProjectStatus
from .forms import ProjectForm, ProjectMemberForm, ProjectPhaseForm

# プロジェクト管理ビュー
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20
    login_url = '/login/'
    
    def get_queryset(self):
        queryset = Project.objects.select_related('manager', 'department').prefetch_related('members')
        
        # 検索機能
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(client__icontains=search)
            )
        
        # ステータスフィルター
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # 部署フィルター
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_statuses'] = ProjectStatus.choices
        
        # 統計情報
        all_projects = Project.objects.all()
        context['stats'] = {
            'total': all_projects.count(),
            'active': all_projects.filter(status=ProjectStatus.ACTIVE).count(),
            'completed': all_projects.filter(status=ProjectStatus.COMPLETED).count(),
            'overdue': sum(1 for p in all_projects if p.is_overdue),
        }
        
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project/project_detail.html'
    context_object_name = 'project'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # プロジェクトメンバー
        context['members'] = project.members.select_related('user').filter(is_active=True)
        
        # プロジェクトフェーズ
        context['phases'] = project.phases.all().order_by('order')
        
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project/project_form.html'
    login_url = '/login/'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'プロジェクト「{form.instance.name}」を作成しました。')
        return super().form_valid(form)

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project/project_form.html'
    login_url = '/login/'
    
    def form_valid(self, form):
        messages.success(self.request, f'プロジェクト「{form.instance.name}」を更新しました。')
        return super().form_valid(form)

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')
    login_url = '/login/'
    
    def delete(self, request, *args, **kwargs):
        project_name = self.get_object().name
        messages.success(request, f'プロジェクト「{project_name}」を削除しました。')
        return super().delete(request, *args, **kwargs)

# プロジェクトメンバー管理ビュー
class ProjectMemberListView(LoginRequiredMixin, ListView):
    model = ProjectMember
    template_name = 'projects/member/project_member_list.html'
    context_object_name = 'members'
    login_url = '/login/'
    
    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return ProjectMember.objects.filter(project=self.project).select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

class ProjectMemberCreateView(LoginRequiredMixin, CreateView):
    model = ProjectMember
    form_class = ProjectMemberForm
    template_name = 'projects/member/project_member_form.html'
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.project = self.project
        messages.success(self.request, f'メンバー「{form.instance.user.username}」を追加しました。')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('projects:project_member_list', kwargs={'project_pk': self.project.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

class ProjectMemberUpdateView(LoginRequiredMixin, UpdateView):
    model = ProjectMember
    form_class = ProjectMemberForm
    template_name = 'projects/member/project_member_form.html'
    login_url = '/login/'
    
    def get_success_url(self):
        return reverse('projects:project_member_list', kwargs={'project_pk': self.object.project.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'メンバー「{form.instance.user.username}」の情報を更新しました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context

class ProjectMemberDeleteView(LoginRequiredMixin, DeleteView):
    model = ProjectMember
    template_name = 'projects/member/project_member_confirm_delete.html'
    login_url = '/login/'
    
    def get_success_url(self):
        return reverse('projects:project_member_list', kwargs={'project_pk': self.object.project.pk})
    
    def delete(self, request, *args, **kwargs):
        member_name = self.get_object().user.username
        messages.success(request, f'メンバー「{member_name}」を削除しました。')
        return super().delete(request, *args, **kwargs)

# プロジェクトフェーズ管理ビュー
class ProjectPhaseListView(LoginRequiredMixin, ListView):
    model = ProjectPhase
    template_name = 'projects/phase/project_phase_list.html'
    context_object_name = 'phases'
    login_url = '/login/'
    
    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return ProjectPhase.objects.filter(project=self.project).order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

class ProjectPhaseCreateView(LoginRequiredMixin, CreateView):
    model = ProjectPhase
    form_class = ProjectPhaseForm
    template_name = 'projects/phase/project_phase_form.html'
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.project = self.project
        messages.success(self.request, f'フェーズ「{form.instance.name}」を追加しました。')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('projects:project_phase_list', kwargs={'project_pk': self.project.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

class ProjectPhaseUpdateView(LoginRequiredMixin, UpdateView):
    model = ProjectPhase
    form_class = ProjectPhaseForm
    template_name = 'projects/phase/project_phase_form.html'
    login_url = '/login/'
    
    def get_success_url(self):
        return reverse('projects:project_phase_list', kwargs={'project_pk': self.object.project.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'フェーズ「{form.instance.name}」を更新しました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context

class ProjectPhaseDeleteView(LoginRequiredMixin, DeleteView):
    model = ProjectPhase
    template_name = 'projects/phase/project_phase_confirm_delete.html'
    login_url = '/login/'
    
    def get_success_url(self):
        return reverse('projects:project_phase_list', kwargs={'project_pk': self.object.project.pk})
    
    def delete(self, request, *args, **kwargs):
        phase_name = self.get_object().name
        messages.success(request, f'フェーズ「{phase_name}」を削除しました。')
        return super().delete(request, *args, **kwargs)

# AJAX用ビュー
@login_required
def load_projects(request):
    """部署選択時にプロジェクトをロードするAJAXビュー"""
    department_id = request.GET.get('department_id')
    projects = Project.objects.filter(
        department_id=department_id,
        is_active=True
    ).order_by('name')
    
    project_list = [{'id': '', 'name': '-- プロジェクトを選択 --'}]
    project_list.extend([
        {'id': project.id, 'name': f"{project.code} - {project.name}"} 
        for project in projects
    ])
    
    return JsonResponse({'projects': project_list})