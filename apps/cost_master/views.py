from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from datetime import date
import json

from apps.core.decorators import (
    leader_or_superuser_required_403,
    LeaderOrSuperuserRequiredMixin
)
from .models import BusinessPartner, OutsourcingCost, OutsourcingCostSummary
from .forms import BusinessPartnerForm, OutsourcingCostForm, OutsourcingCostFilterForm
from apps.projects.models import Project, ProjectTicket


# ダッシュボード
@login_required
@leader_or_superuser_required_403
def outsourcing_dashboard(request):
    """外注費管理ダッシュボード"""
    current_month = date.today().strftime('%Y-%m')
    
    # 当月の集計
    current_summary = OutsourcingCostSummary.calculate_summary(current_month)
    
    # 最近の外注費レコード
    recent_costs = OutsourcingCost.objects.select_related(
        'business_partner', 'project', 'ticket'
    ).order_by('-created_at')[:10]
    
    # アクティブなBP数
    active_bp_count = BusinessPartner.objects.filter(is_active=True).count()
    
    # 月別集計（直近6ヶ月）
    monthly_summaries = OutsourcingCostSummary.objects.order_by('-year_month')[:6]
    
    context = {
        'current_month': current_month,
        'current_summary': current_summary,
        'recent_costs': recent_costs,
        'active_bp_count': active_bp_count,
        'monthly_summaries': monthly_summaries,
    }
    
    return render(request, 'cost_master/dashboard.html', context)


# ビジネスパートナー管理
class BusinessPartnerListView(LeaderOrSuperuserRequiredMixin, ListView):
    """ビジネスパートナー一覧"""
    model = BusinessPartner
    template_name = 'cost_master/business_partner_list.html'
    context_object_name = 'business_partners'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = BusinessPartner.objects.filter(is_active=True).select_related().prefetch_related('projects')

        # 検索フィルター
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(company__icontains=search) |
                Q(email__icontains=search)
            )
        
        # 有効/無効フィルター
        status = self.request.GET.get('status', 'active')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', 'active')
        return context


class BusinessPartnerCreateView(LeaderOrSuperuserRequiredMixin, CreateView):
    """ビジネスパートナー作成"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'cost_master/business_partner_form.html'
    success_url = reverse_lazy('cost_master:business_partner_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'ビジネスパートナーを登録しました。')
        return super().form_valid(form)


class BusinessPartnerUpdateView(LeaderOrSuperuserRequiredMixin, UpdateView):
    """ビジネスパートナー編集"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'cost_master/business_partner_form.html'
    success_url = reverse_lazy('cost_master:business_partner_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'ビジネスパートナー情報を更新しました。')
        return super().form_valid(form)


@login_required
@leader_or_superuser_required_403
def business_partner_delete(request, pk):
    """ビジネスパートナー削除"""
    bp = get_object_or_404(BusinessPartner, pk=pk)
    
    if request.method == 'POST':
        bp.is_active = False
        bp.save()
        messages.success(request, f'{bp.name}を無効化しました。')
        return redirect('cost_master:business_partner_list')
    
    return render(request, 'cost_master/business_partner_confirm_delete.html', {'object': bp})


# 外注費管理
@login_required
@leader_or_superuser_required_403
def outsourcing_cost_list(request):
    """外注費一覧・管理画面"""
    # フィルターフォーム
    filter_form = OutsourcingCostFilterForm(request.GET)
    
    # 基本クエリセット
    queryset = OutsourcingCost.objects.select_related(
        'business_partner', 'project', 'ticket'
    )
    
    # フィルター適用
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('year_month'):
            queryset = queryset.filter(year_month=filter_form.cleaned_data['year_month'])
        if filter_form.cleaned_data.get('business_partner'):
            queryset = queryset.filter(business_partner=filter_form.cleaned_data['business_partner'])
        if filter_form.cleaned_data.get('project'):
            queryset = queryset.filter(project=filter_form.cleaned_data['project'])
        if filter_form.cleaned_data.get('status'):
            queryset = queryset.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data.get('case_classification'):
            queryset = queryset.filter(case_classification=filter_form.cleaned_data['case_classification'])
    
    # 並び順
    queryset = queryset.order_by('-year_month', 'business_partner__name')
    
    # ページネーション
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 集計情報
    total_costs = queryset.aggregate(
        total_hours=Sum('work_hours'),
        total_amount=Sum('total_cost'),
        count=Count('id')
    )
    
    context = {
        'filter_form': filter_form,
        'page_obj': page_obj,
        'total_costs': total_costs,
    }
    
    return render(request, 'cost_master/outsourcing_cost_list.html', context)


@login_required
@leader_or_superuser_required_403
def outsourcing_cost_create(request):
    """外注費登録"""
    if request.method == 'POST':
        form = OutsourcingCostForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            instance.save()
            
            # 月次集計を更新
            OutsourcingCostSummary.calculate_summary(instance.year_month)
            
            messages.success(request, '外注費を登録しました。')
            return redirect('cost_master:outsourcing_cost_list')
    else:
        form = OutsourcingCostForm()
    
    context = {
        'form': form,
        'title': '外注費登録',
        'submit_text': '登録'
    }
    
    return render(request, 'cost_master/outsourcing_cost_form.html', context)


@login_required
@leader_or_superuser_required_403
def outsourcing_cost_update(request, pk):
    """外注費編集"""
    cost = get_object_or_404(OutsourcingCost, pk=pk)
    
    if request.method == 'POST':
        form = OutsourcingCostForm(request.POST, instance=cost)
        if form.is_valid():
            old_year_month = cost.year_month
            instance = form.save()
            
            # 旧月と新月の集計を更新
            OutsourcingCostSummary.calculate_summary(old_year_month)
            if instance.year_month != old_year_month:
                OutsourcingCostSummary.calculate_summary(instance.year_month)
            
            messages.success(request, '外注費を更新しました。')
            return redirect('cost_master:outsourcing_cost_list')
    else:
        form = OutsourcingCostForm(instance=cost)
    
    context = {
        'form': form,
        'object': cost,
        'title': '外注費編集',
        'submit_text': '更新'
    }
    
    return render(request, 'cost_master/outsourcing_cost_form.html', context)


@login_required
@leader_or_superuser_required_403
def outsourcing_cost_delete(request, pk):
    """外注費削除"""
    cost = get_object_or_404(OutsourcingCost, pk=pk)
    
    if request.method == 'POST':
        year_month = cost.year_month
        cost.delete()
        
        # 月次集計を更新
        OutsourcingCostSummary.calculate_summary(year_month)
        
        messages.success(request, '外注費を削除しました。')
        return redirect('cost_master:outsourcing_cost_list')
    
    return render(request, 'cost_master/outsourcing_cost_confirm_delete.html', {'object': cost})


# API エンドポイント
@login_required
@leader_or_superuser_required_403
def get_project_tickets_api(request):
    """プロジェクトのチケット一覧取得API"""
    project_id = request.GET.get('project_id')
    
    if not project_id:
        return JsonResponse({'success': False, 'tickets': []})
    
    try:
        tickets = ProjectTicket.objects.filter(
            project_id=project_id,
            is_active=True
        ).values('id', 'title', 'case_classification').order_by('title')
        
        return JsonResponse({
            'success': True,
            'tickets': list(tickets)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'tickets': []
        })


@login_required
def get_bp_hourly_rate_api(request):
    """ビジネスパートナーの単価取得API"""
    bp_id = request.GET.get('bp_id')
    
    if not bp_id:
        return JsonResponse({'success': False, 'hourly_rate': 0})
    
    try:
        bp = BusinessPartner.objects.get(id=bp_id, is_active=True)
        return JsonResponse({
            'success': True,
            'hourly_rate': float(bp.hourly_rate)
        })
    except BusinessPartner.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'ビジネスパートナーが見つかりません',
            'hourly_rate': 0
        })


@login_required
@leader_or_superuser_required_403
def get_bp_projects_api(request):
    """ビジネスパートナーの参加プロジェクト取得API"""
    bp_id = request.GET.get('bp_id')
    
    if not bp_id:
        return JsonResponse({'success': False, 'projects': []})
    
    try:
        bp = BusinessPartner.objects.get(id=bp_id, is_active=True)
        projects = bp.projects.filter(is_active=True).values(
            'id', 'name'
        ).order_by('name')
        
        return JsonResponse({
            'success': True,
            'projects': list(projects)
        })
    except BusinessPartner.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'ビジネスパートナーが見つかりません',
            'projects': []
        })


@login_required
@leader_or_superuser_required_403
def get_ticket_outsourcing_cost_api(request):
    """チケットの外注費取得API"""
    ticket_id = request.GET.get('ticket_id')
    year_month = request.GET.get('year_month')
    
    if not ticket_id:
        return JsonResponse({'success': False, 'total_cost': 0})
    
    try:
        # 指定チケットの外注費を集計
        outsourcing_costs = OutsourcingCost.objects.filter(
            ticket_id=ticket_id,
            status='in_progress'  # 着手案件のみ
        )
        
        if year_month:
            outsourcing_costs = outsourcing_costs.filter(year_month=year_month)
        
        # 総外注費を計算
        total_cost = sum(cost.total_cost for cost in outsourcing_costs)
        
        # 詳細情報も含める
        cost_details = []
        for cost in outsourcing_costs:
            cost_details.append({
                'year_month': cost.year_month,
                'business_partner': cost.business_partner.name,
                'work_hours': float(cost.work_hours),
                'hourly_rate': float(cost.hourly_rate),
                'total_cost': float(cost.total_cost)
            })
        
        return JsonResponse({
            'success': True,
            'total_cost': float(total_cost),
            'cost_details': cost_details,
            'count': len(cost_details)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'total_cost': 0
        })