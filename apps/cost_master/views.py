from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg
from datetime import date, datetime, timedelta

from .models import CostMaster  # 存在するモデルのみインポート
from .forms import CostMasterForm
from apps.users.models import Department, CustomUser

@method_decorator(staff_member_required, name='dispatch')
class CostMasterListView(LoginRequiredMixin, ListView):
    """コストマスター一覧画面"""
    model = CostMaster
    template_name = 'cost_master/cost_master_list.html'
    context_object_name = 'cost_masters'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CostMaster.objects.select_related('department', 'manager').order_by('-created_at')
        
        # 検索フィルター
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(client_name__icontains=search) |
                Q(special_conditions__icontains=search) |
                Q(payment_terms__icontains=search)
            )
        
        # フィルター処理
        billing_type = self.request.GET.get('billing_type')
        if billing_type:
            queryset = queryset.filter(billing_type=billing_type)
        
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        
        contract_type = self.request.GET.get('contract_type')
        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)
        
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # フィルター用データ
        context['departments'] = Department.objects.all()
        context['billing_types'] = CostMaster.BILLING_TYPE_CHOICES
        context['contract_types'] = CostMaster.CONTRACT_TYPE_CHOICES
        
        # 統計データ
        total_count = CostMaster.objects.count()
        active_count = CostMaster.objects.filter(is_active=True).count()
        context['stats'] = {
            'total': total_count,
            'active': active_count,
            'inactive': total_count - active_count,
        }
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class CostMasterCreateView(LoginRequiredMixin, CreateView):
    """コストマスター作成画面"""
    model = CostMaster
    form_class = CostMasterForm
    template_name = 'cost_master/cost_master_form.html'
    success_url = reverse_lazy('cost_master:cost_master_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'コストマスター「{form.cleaned_data["client_name"]}」が正常に作成されました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'コストマスター - 新規作成'
        
        # 複製の場合
        copy_id = self.request.GET.get('copy')
        if copy_id:
            try:
                original = CostMaster.objects.get(pk=copy_id)
                context['title'] = f'コストマスター - 複製作成（元: {original.client_name}）'
                context['copy_source'] = original
            except CostMaster.DoesNotExist:
                pass
        
        return context
    
    def get_initial(self):
        initial = super().get_initial()
        
        # 複製の場合
        copy_id = self.request.GET.get('copy')
        if copy_id:
            try:
                original = CostMaster.objects.get(pk=copy_id)
                initial.update({
                    'client_name': f"{original.client_name}_コピー",
                    'billing_type': original.billing_type,
                    'department': original.department,
                    'employee_level': original.employee_level,
                    'monthly_billing': original.monthly_billing,
                    'daily_billing': original.daily_billing,
                    'hourly_billing': original.hourly_billing,
                    'fixed_billing': original.fixed_billing,
                    'discount_rate': original.discount_rate,
                    'minimum_billing_amount': original.minimum_billing_amount,
                    'contract_type': original.contract_type,
                    'payment_terms': original.payment_terms,
                    'effective_from': date.today(),
                    'is_active': True,
                })
            except CostMaster.DoesNotExist:
                pass
        
        return initial

@method_decorator(staff_member_required, name='dispatch')
class CostMasterDetailView(LoginRequiredMixin, DetailView):
    """コストマスター詳細画面"""
    model = CostMaster
    template_name = 'cost_master/cost_master_detail.html'
    context_object_name = 'cost_master'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 換算計算
        cost_master = self.object
        conversions = {}
        
        if cost_master.billing_type == 'monthly' and cost_master.monthly_billing:
            conversions['monthly'] = float(cost_master.monthly_billing)
            conversions['daily'] = float(cost_master.monthly_billing) / 20
            conversions['hourly'] = float(cost_master.monthly_billing) * 10000 / 20 / 8
        elif cost_master.billing_type == 'daily' and cost_master.daily_billing:
            conversions['monthly'] = float(cost_master.daily_billing) * 20
            conversions['daily'] = float(cost_master.daily_billing)
            conversions['hourly'] = float(cost_master.daily_billing) * 10000 / 8
        elif cost_master.billing_type == 'hourly' and cost_master.hourly_billing:
            conversions['monthly'] = float(cost_master.hourly_billing) * 8 * 20 / 10000
            conversions['daily'] = float(cost_master.hourly_billing) * 8 / 10000
            conversions['hourly'] = float(cost_master.hourly_billing)
        elif cost_master.billing_type == 'fixed' and cost_master.fixed_billing:
            conversions['monthly'] = float(cost_master.fixed_billing)
            conversions['daily'] = None
            conversions['hourly'] = None
        else:
            conversions = {'monthly': None, 'daily': None, 'hourly': None}
        
        context['conversions'] = conversions
        
        # 割引後単価の計算例
        if conversions['monthly']:
            sample_amount = conversions['monthly']
            context['discounted_amount'] = cost_master.get_discounted_billing(sample_amount)
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class CostMasterUpdateView(LoginRequiredMixin, UpdateView):
    """コストマスター編集画面"""
    model = CostMaster
    form_class = CostMasterForm
    template_name = 'cost_master/cost_master_form.html'
    success_url = reverse_lazy('cost_master:cost_master_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'コストマスター「{form.cleaned_data["client_name"]}」が正常に更新されました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'コストマスター - 編集'
        return context

@method_decorator(staff_member_required, name='dispatch')
class CostMasterDeleteView(LoginRequiredMixin, DeleteView):
    """コストマスター削除画面"""
    model = CostMaster
    template_name = 'cost_master/cost_master_confirm_delete.html'
    success_url = reverse_lazy('cost_master:cost_master_list')
    
    def delete(self, request, *args, **kwargs):
        client_name = self.get_object().client_name
        messages.success(request, f'コストマスター「{client_name}」を削除しました。')
        return super().delete(request, *args, **kwargs)

# 案件別コスト設定関連（仮実装）
@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingListView(LoginRequiredMixin, ListView):
    """案件別コスト設定一覧画面（仮実装）"""
    template_name = 'cost_master/project_cost_setting_list.html'
    context_object_name = 'project_settings'
    paginate_by = 20
    
    def get_queryset(self):
        # 現在は空のリストを返す（将来的にプロジェクト管理機能と連携）
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '案件別コスト設定'
        return context

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingCreateView(LoginRequiredMixin, CreateView):
    """案件別コスト設定作成画面（仮実装）"""
    template_name = 'cost_master/project_cost_setting_form.html'
    success_url = reverse_lazy('cost_master:project_cost_setting_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '案件別コスト設定 - 新規作成'
        return context

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingDetailView(LoginRequiredMixin, DetailView):
    """案件別コスト設定詳細画面（仮実装）"""
    template_name = 'cost_master/project_cost_setting_detail.html'
    context_object_name = 'project_setting'
    
    def get_object(self):
        # 仮の実装
        return None

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingUpdateView(LoginRequiredMixin, UpdateView):
    """案件別コスト設定編集画面（仮実装）"""
    template_name = 'cost_master/project_cost_setting_form.html'
    success_url = reverse_lazy('cost_master:project_cost_setting_list')

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingDeleteView(LoginRequiredMixin, DeleteView):
    """案件別コスト設定削除画面（仮実装）"""
    template_name = 'cost_master/project_cost_setting_confirm_delete.html'
    success_url = reverse_lazy('cost_master:project_cost_setting_list')

# AJAX API
@staff_member_required
def get_cost_master_data(request):
    """コストマスターデータ取得API"""
    cost_masters = CostMaster.objects.filter(is_active=True).select_related('department')
    
    data = []
    for cm in cost_masters:
        data.append({
            'id': cm.id,
            'client_name': cm.client_name,
            'billing_type': cm.get_billing_type_display(),
            'billing_amount': cm.get_billing_amount(),
            'department': cm.department.name if cm.department else '全部署',
            'contract_type': cm.get_contract_type_display(),
        })
    
    return JsonResponse({'data': data})

@staff_member_required
def cost_analysis_data(request):
    """コスト分析データ取得API"""
    # 基本統計
    stats = {
        'total_clients': CostMaster.objects.values('client_name').distinct().count(),
        'active_contracts': CostMaster.objects.filter(is_active=True).count(),
        'avg_discount': CostMaster.objects.aggregate(avg_discount=Avg('discount_rate'))['avg_discount'] or 0,
    }
    
    # 請求タイプ別分布
    billing_type_dist = list(
        CostMaster.objects.values('billing_type')
        .annotate(count=Count('id'))
        .order_by('billing_type')
    )
    
    # 契約タイプ別分布
    contract_type_dist = list(
        CostMaster.objects.values('contract_type')
        .annotate(count=Count('id'))
        .order_by('contract_type')
    )
    
    return JsonResponse({
        'stats': stats,
        'billing_type_distribution': billing_type_dist,
        'contract_type_distribution': contract_type_dist,
    })