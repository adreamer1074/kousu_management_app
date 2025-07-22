from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import date, datetime, timedelta
from django.contrib.auth import get_user_model

from .models import ReportExport, WorkloadAggregation
from .forms import WorkloadAggregationForm, WorkloadAggregationFilterForm
from apps.users.models import Department

User = get_user_model()

class WorkloadAggregationListView(LoginRequiredMixin, ListView):
    """工数集計一覧画面（工数集計レポート機能）"""
    model = WorkloadAggregation
    template_name = 'reports/workload_aggregation.html'
    context_object_name = 'aggregated_projects'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = WorkloadAggregation.objects.select_related(
            'project', 'project_detail', 'department', 'manager', 'created_by'
        ).order_by('-year_month', '-created_at')
        
        # フィルター処理
        form = WorkloadAggregationFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('year_month'):
                queryset = queryset.filter(year_month=form.cleaned_data['year_month'])
            if form.cleaned_data.get('project'):
                queryset = queryset.filter(project=form.cleaned_data['project'])
            if form.cleaned_data.get('department'):
                queryset = queryset.filter(department=form.cleaned_data['department'])
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('manager'):
                queryset = queryset.filter(manager=form.cleaned_data['manager'])
            if form.cleaned_data.get('search'):
                search_term = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(project__name__icontains=search_term) |
                    Q(notes__icontains=search_term)
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # フィルターフォーム
        context['filter_form'] = WorkloadAggregationFilterForm(self.request.GET)
        
        # 統計データ
        queryset = self.get_queryset()
        context['total_stats'] = {
            'total_budget': queryset.aggregate(total=Sum('budget'))['total'] or 0,
            'total_billing': queryset.aggregate(total=Sum('billing_amount'))['total'] or 0,
            'total_outsourcing': queryset.aggregate(total=Sum('outsourcing_cost'))['total'] or 0,
            'total_estimated_workdays': queryset.aggregate(total=Sum('estimated_workdays'))['total'] or 0,
            'total_used_workdays': queryset.aggregate(total=Sum('used_workdays'))['total'] or 0,
        }
        
        # 現在のフィルター値
        context['current_filters'] = {
            'year_month': self.request.GET.get('year_month', ''),
            'project_id': self.request.GET.get('project', ''),
            'department_id': self.request.GET.get('department', ''),
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        return context

class WorkloadAggregationCreateView(LoginRequiredMixin, CreateView):
    """工数集計作成画面"""
    model = WorkloadAggregation
    form_class = WorkloadAggregationForm
    template_name = 'reports/workload_aggregation_form.html'
    success_url = reverse_lazy('reports:workload_aggregation')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '工数集計データが正常に登録されました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '工数集計 - 新規登録'
        return context

class WorkloadAggregationDetailView(LoginRequiredMixin, DetailView):
    """工数集計詳細画面"""
    model = WorkloadAggregation
    template_name = 'reports/workload_aggregation_detail.html'
    context_object_name = 'workload_aggregation'

class WorkloadAggregationUpdateView(LoginRequiredMixin, UpdateView):
    """工数集計編集画面"""
    model = WorkloadAggregation
    form_class = WorkloadAggregationForm
    template_name = 'reports/workload_aggregation_form.html'
    success_url = reverse_lazy('reports:workload_aggregation')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, '工数集計データが正常に更新されました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '工数集計 - 編集'
        return context

class WorkloadAggregationDeleteView(LoginRequiredMixin, DeleteView):
    """工数集計削除画面"""
    model = WorkloadAggregation
    template_name = 'reports/workload_aggregation_confirm_delete.html'
    success_url = reverse_lazy('reports:workload_aggregation')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '工数集計データを削除しました。')
        return super().delete(request, *args, **kwargs)

@login_required
def workload_export(request):
    """工数データのエクスポート"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    # CSV レスポンスの作成
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="workload_aggregation_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    # BOM付きでUTF-8エンコーディング
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow([
        'プロジェクト名', '年月', 'ステータス', '予算（万円）', '請求金額（万円）',
        '外注費（万円）', '見積工数（人日）', '消化工数（人日）', '進捗率（%）',
        '担当部署', 'プロジェクトマネージャー', '作成日時'
    ])
    
    # フィルター適用
    queryset = WorkloadAggregation.objects.select_related(
        'project', 'department', 'manager'
    ).order_by('-year_month')
    
    # URLパラメータでフィルター
    if request.GET.get('year_month'):
        queryset = queryset.filter(year_month=request.GET['year_month'])
    if request.GET.get('project'):
        queryset = queryset.filter(project_id=request.GET['project'])
    if request.GET.get('status'):
        queryset = queryset.filter(status=request.GET['status'])
    
    for workload in queryset:
        writer.writerow([
            workload.project.name,
            workload.year_month,
            workload.get_status_display(),
            str(workload.budget),
            str(workload.billing_amount),
            str(workload.outsourcing_cost),
            str(workload.estimated_workdays),
            str(workload.used_workdays),
            workload.progress_rate,
            workload.department.name if workload.department else '',
            workload.manager.get_full_name() if workload.manager else '',
            workload.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response

# 既存のビューは保持
class ReportListView(LoginRequiredMixin, TemplateView):
    """レポート一覧画面"""
    template_name = 'reports/report_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # レポートメニューの定義
        reports = [
            {
                'name': '工数集計レポート',
                'description': '工数集計一覧の管理と分析',
                'url': 'reports:workload_aggregation',
                'icon': 'bi-bar-chart-line',
                'color': 'success'
            },
            {
                'name': 'エクスポート履歴',
                'description': 'レポートのエクスポート履歴',
                'url': 'reports:report_export_list',
                'icon': 'bi-download',
                'color': 'info'
            },
        ]
        
        context['reports'] = reports
        return context

class ReportExportListView(LoginRequiredMixin, ListView):
    """レポートエクスポート一覧画面"""
    model = ReportExport
    template_name = 'reports/report_export_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        return ReportExport.objects.select_related('created_by').order_by('-created_at')