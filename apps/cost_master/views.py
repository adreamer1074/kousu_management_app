from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from datetime import datetime, date
import json

from .models import CostMaster, ClientBillingRate, ProjectCostSetting
from .forms import CostMasterForm, ClientBillingRateForm, ProjectCostSettingForm
from apps.users.models import Department
from apps.projects.models import ProjectDetail

@method_decorator(staff_member_required, name='dispatch')
class CostMasterListView(LoginRequiredMixin, ListView):
    """コストマスター一覧画面"""
    model = CostMaster
    template_name = 'cost_master/cost_master_list.html'
    context_object_name = 'cost_masters'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CostMaster.objects.select_related('department')
        
        # フィルター処理
        department_id = self.request.GET.get('department')
        employee_level = self.request.GET.get('employee_level')
        billing_type = self.request.GET.get('billing_type')
        is_active = self.request.GET.get('is_active')
        search = self.request.GET.get('search')
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if employee_level:
            queryset = queryset.filter(employee_level=employee_level)
        if billing_type:
            queryset = queryset.filter(billing_type=billing_type)
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        if search:
            queryset = queryset.filter(
                Q(department__name__icontains=search)
            )
        
        return queryset.order_by('-effective_from', 'department__name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # フィルターオプション
        context['departments'] = Department.objects.filter(is_active=True)
        context['employee_levels'] = CostMaster.EMPLOYEE_LEVEL_CHOICES
        context['billing_types'] = CostMaster.BILLING_TYPE_CHOICES
        
        # 現在のフィルター値
        context['current_filters'] = {
            'department': self.request.GET.get('department', ''),
            'employee_level': self.request.GET.get('employee_level', ''),
            'billing_type': self.request.GET.get('billing_type', ''),
            'is_active': self.request.GET.get('is_active', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        # 統計情報
        context['stats'] = {
            'total_count': CostMaster.objects.count(),
            'active_count': CostMaster.objects.filter(is_active=True).count(),
            'departments_count': CostMaster.objects.values('department').distinct().count(),
            'avg_profit_margin': self.get_average_profit_margin(),
        }
        
        return context
    
    def get_average_profit_margin(self):
        """平均利益率を計算"""
        cost_masters = CostMaster.objects.filter(is_active=True)
        if not cost_masters.exists():
            return 0
        
        total_margin = sum(cm.profit_margin for cm in cost_masters)
        return round(total_margin / cost_masters.count(), 1)

@method_decorator(staff_member_required, name='dispatch')
class CostMasterCreateView(LoginRequiredMixin, CreateView):
    """コストマスター作成画面"""
    model = CostMaster
    form_class = CostMasterForm
    template_name = 'cost_master/cost_master_form.html'
    success_url = reverse_lazy('cost_master:cost_master_list')
    
    def get_initial(self):
        initial = super().get_initial()
        
        # 複製機能：copy パラメータがある場合
        copy_id = self.request.GET.get('copy')
        if copy_id:
            try:
                source_cost = CostMaster.objects.get(pk=copy_id)
                initial.update({
                    'department': source_cost.department,
                    'employee_level': source_cost.employee_level,
                    'billing_type': source_cost.billing_type,
                    'monthly_cost': source_cost.monthly_cost,
                    'monthly_billing': source_cost.monthly_billing,
                    'daily_cost': source_cost.daily_cost,
                    'daily_billing': source_cost.daily_billing,
                    'hourly_cost': source_cost.hourly_cost,
                    'hourly_billing': source_cost.hourly_billing,
                    'fixed_cost': source_cost.fixed_cost,
                    'fixed_billing': source_cost.fixed_billing,
                    'overtime_rate': source_cost.overtime_rate,
                    'holiday_rate': source_cost.holiday_rate,
                    'is_active': True,  # 新規作成時は常に有効
                })
            except CostMaster.DoesNotExist:
                pass
        
        return initial
    
    def form_valid(self, form):
        messages.success(self.request, 'コストマスターが正常に作成されました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新規コストマスター作成'
        context['button_text'] = '作成'
        
        # 複製の場合は表示を変更
        if self.request.GET.get('copy'):
            context['title'] = 'コストマスター複製作成'
            
        return context

@method_decorator(staff_member_required, name='dispatch')
class CostMasterUpdateView(LoginRequiredMixin, UpdateView):
    """コストマスター編集画面"""
    model = CostMaster
    form_class = CostMasterForm
    template_name = 'cost_master/cost_master_form.html'
    success_url = reverse_lazy('cost_master:cost_master_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'コストマスターが正常に更新されました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'コストマスター編集'
        context['button_text'] = '更新'
        return context

@method_decorator(staff_member_required, name='dispatch')
class CostMasterDetailView(LoginRequiredMixin, DetailView):
    """コストマスター詳細画面"""
    model = CostMaster
    template_name = 'cost_master/cost_master_detail.html'
    context_object_name = 'cost_master'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 関連するプロジェクト数
        context['related_projects_count'] = ProjectDetail.objects.filter(
            department=self.object.department
        ).count()
        
        # 今日の日付
        from datetime import date
        context['today'] = date.today()
        
        # 換算計算
        cost_master = self.object
        conversions = {}
        
        if cost_master.billing_type == 'monthly':
            conversions['monthly'] = float(cost_master.monthly_billing)
            conversions['daily'] = float(cost_master.monthly_billing) / 20
            conversions['hourly'] = float(cost_master.monthly_billing) * 10000 / 20 / 8
        elif cost_master.billing_type == 'daily':
            conversions['monthly'] = float(cost_master.daily_billing) * 20
            conversions['daily'] = float(cost_master.daily_billing)
            conversions['hourly'] = float(cost_master.daily_billing) * 10000 / 8
        elif cost_master.billing_type == 'hourly':
            conversions['monthly'] = float(cost_master.hourly_billing) * 8 * 20 / 10000
            conversions['daily'] = float(cost_master.hourly_billing) * 8 / 10000
            conversions['hourly'] = float(cost_master.hourly_billing)
        elif cost_master.billing_type == 'fixed':
            conversions['monthly'] = float(cost_master.fixed_billing)
            conversions['daily'] = None
            conversions['hourly'] = None
        
        context['conversions'] = conversions
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class ClientBillingRateListView(LoginRequiredMixin, ListView):
    """取引先別請求単価一覧画面"""
    model = ClientBillingRate
    template_name = 'cost_master/client_billing_rate_list.html'
    context_object_name = 'billing_rates'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = ClientBillingRate.objects.select_related('department').order_by('-created_at')
        
        # フィルター処理
        client_name = self.request.GET.get('client_name')
        if client_name:
            queryset = queryset.filter(client_name__icontains=client_name)
        
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
        
        has_discount = self.request.GET.get('has_discount')
        if has_discount == 'true':
            queryset = queryset.filter(discount_rate__gt=0)
        elif has_discount == 'false':
            queryset = queryset.filter(discount_rate=0)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 部署一覧
        context['departments'] = Department.objects.all()
        
        # 契約タイプ選択肢
        context['contract_types'] = ClientBillingRate._meta.get_field('contract_type').choices
        
        # 既存の取引先名一覧
        context['client_names'] = list(
            ClientBillingRate.objects.values_list('client_name', flat=True).distinct()
        )
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class ClientBillingRateCreateView(LoginRequiredMixin, CreateView):
    """取引先別請求単価作成画面"""
    model = ClientBillingRate
    form_class = ClientBillingRateForm
    template_name = 'cost_master/client_billing_rate_form.html'
    success_url = reverse_lazy('cost_master:client_billing_rate_list')
    
    def get_initial(self):
        initial = super().get_initial()
        
        # 複製機能
        copy_id = self.request.GET.get('copy')
        if copy_id:
            try:
                source_rate = ClientBillingRate.objects.get(pk=copy_id)
                initial.update({
                    'department': source_rate.department,
                    'employee_level': source_rate.employee_level,
                    'billing_type': source_rate.billing_type,
                    'monthly_billing': source_rate.monthly_billing,
                    'daily_billing': source_rate.daily_billing,
                    'hourly_billing': source_rate.hourly_billing,
                    'fixed_billing': source_rate.fixed_billing,
                    'discount_rate': source_rate.discount_rate,
                    'minimum_billing_amount': source_rate.minimum_billing_amount,
                    'contract_type': source_rate.contract_type,
                    'payment_terms': source_rate.payment_terms,
                    'is_active': True,
                })
            except ClientBillingRate.DoesNotExist:
                pass
        
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 既存の取引先名リスト
        context['existing_clients'] = list(
            ClientBillingRate.objects.values_list('client_name', flat=True).distinct()
        )
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'取引先「{form.cleaned_data["client_name"]}」が正常に登録されました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '入力内容にエラーがあります。確認してください。')
        return super().form_invalid(form)

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingListView(LoginRequiredMixin, ListView):
    """案件別コスト設定一覧画面"""
    template_name = 'cost_master/project_cost_setting_list.html'
    context_object_name = 'project_settings'
    paginate_by = 20
    
    def get_queryset(self):
        # 仮の実装（プロジェクト関連データがある場合に調整）
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '案件別コスト設定'
        return context

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingCreateView(LoginRequiredMixin, CreateView):
    """案件別コスト設定作成画面"""
    template_name = 'cost_master/project_cost_setting_form.html'
    success_url = reverse_lazy('cost_master:project_cost_setting_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '案件別コスト設定 - 新規作成'
        return context

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingDetailView(LoginRequiredMixin, DetailView):
    """案件別コスト設定詳細画面"""
    template_name = 'cost_master/project_cost_setting_detail.html'
    context_object_name = 'project_setting'
    
    def get_object(self):
        # 仮の実装
        return None

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingUpdateView(LoginRequiredMixin, UpdateView):
    """案件別コスト設定編集画面"""
    template_name = 'cost_master/project_cost_setting_form.html'
    success_url = reverse_lazy('cost_master:project_cost_setting_list')

@method_decorator(staff_member_required, name='dispatch')
class ProjectCostSettingDeleteView(LoginRequiredMixin, DeleteView):
    """案件別コスト設定削除画面"""
    template_name = 'cost_master/project_cost_setting_confirm_delete.html'
    success_url = reverse_lazy('cost_master:project_cost_setting_list')

# AJAX API ビュー
@staff_member_required
def get_cost_master_data(request):
    """コストマスターデータをJSON形式で返す"""
    department_id = request.GET.get('department_id')
    employee_level = request.GET.get('employee_level')
    
    cost_masters = CostMaster.objects.filter(
        department_id=department_id,
        employee_level=employee_level,
        is_active=True
    ).order_by('-effective_from')
    
    data = []
    for cm in cost_masters:
        data.append({
            'id': cm.id,
            'billing_type': cm.billing_type,
            'monthly_cost': float(cm.monthly_cost),
            'monthly_billing': float(cm.monthly_billing),
            'daily_cost': float(cm.daily_cost),
            'daily_billing': float(cm.daily_billing),
            'hourly_cost': float(cm.hourly_cost),
            'hourly_billing': float(cm.hourly_billing),
            'profit_margin': float(cm.profit_margin),
            'effective_from': cm.effective_from.strftime('%Y-%m-%d'),
        })
    
    return JsonResponse({'cost_masters': data})

@staff_member_required
def cost_analysis_data(request):
    """コスト分析データをJSON形式で返す"""
    # 部署別利益率
    departments_data = []
    for dept in Department.objects.filter(is_active=True):
        cost_masters = CostMaster.objects.filter(department=dept, is_active=True)
        if cost_masters.exists():
            avg_margin = sum(cm.profit_margin for cm in cost_masters) / cost_masters.count()
            departments_data.append({
                'name': dept.name,
                'avg_profit_margin': round(avg_margin, 1),
                'cost_masters_count': cost_masters.count()
            })
    
    # 社員レベル別平均単価
    levels_data = []
    for level, level_display in CostMaster.EMPLOYEE_LEVEL_CHOICES:
        cost_masters = CostMaster.objects.filter(employee_level=level, is_active=True)
        if cost_masters.exists():
            avg_monthly_billing = sum(cm.monthly_billing for cm in cost_masters) / cost_masters.count()
            levels_data.append({
                'level': level_display,
                'avg_monthly_billing': round(float(avg_monthly_billing), 1)
            })
    
    return JsonResponse({
        'departments': departments_data,
        'employee_levels': levels_data
    })

@method_decorator(staff_member_required, name='dispatch')
class ClientBillingRateDetailView(LoginRequiredMixin, DetailView):
    """取引先別請求単価詳細画面"""
    model = ClientBillingRate
    template_name = 'cost_master/client_billing_rate_detail.html'
    context_object_name = 'client_rate'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 関連するプロジェクト数
        context['related_projects_count'] = ProjectDetail.objects.filter(
            billing_destination=self.object.client_name
        ).count()
        
        # 今日の日付
        from datetime import date
        context['today'] = date.today()
        
        # 換算計算
        client_rate = self.object
        conversions = {}
        
        if client_rate.billing_type == 'monthly' and client_rate.monthly_billing:
            conversions['monthly'] = float(client_rate.monthly_billing)
            conversions['daily'] = float(client_rate.monthly_billing) / 20
            conversions['hourly'] = float(client_rate.monthly_billing) * 10000 / 20 / 8
        elif client_rate.billing_type == 'daily' and client_rate.daily_billing:
            conversions['monthly'] = float(client_rate.daily_billing) * 20
            conversions['daily'] = float(client_rate.daily_billing)
            conversions['hourly'] = float(client_rate.daily_billing) * 10000 / 8
        elif client_rate.billing_type == 'hourly' and client_rate.hourly_billing:
            conversions['monthly'] = float(client_rate.hourly_billing) * 8 * 20 / 10000
            conversions['daily'] = float(client_rate.hourly_billing) * 8 / 10000
            conversions['hourly'] = float(client_rate.hourly_billing)
        elif client_rate.billing_type == 'fixed' and client_rate.fixed_billing:
            conversions['monthly'] = float(client_rate.fixed_billing)
            conversions['daily'] = None
            conversions['hourly'] = None
        else:
            conversions = {'monthly': None, 'daily': None, 'hourly': None}
        
        context['conversions'] = conversions
        
        # 割引後単価の計算例
        if conversions['monthly']:
            sample_amount = conversions['monthly']
            context['discounted_amount'] = client_rate.get_discounted_billing(sample_amount)
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class ClientBillingRateUpdateView(LoginRequiredMixin, UpdateView):
    """取引先別請求単価編集画面"""
    model = ClientBillingRate
    form_class = ClientBillingRateForm
    template_name = 'cost_master/client_billing_rate_form.html'
    success_url = reverse_lazy('cost_master:client_billing_rate_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'取引先「{form.cleaned_data["client_name"]}」が正常に更新されました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '取引先別請求単価編集'
        context['button_text'] = '更新'
        
        # 既存の取引先名リスト
        context['existing_clients'] = list(
            ClientBillingRate.objects.values_list('client_name', flat=True).distinct()
        )
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class ClientBillingRateDeleteView(LoginRequiredMixin, DeleteView):
    """取引先別請求単価削除画面"""
    model = ClientBillingRate
    template_name = 'cost_master/client_billing_rate_confirm_delete.html'
    success_url = reverse_lazy('cost_master:client_billing_rate_list')
    
    def delete(self, request, *args, **kwargs):
        client_name = self.get_object().client_name
        messages.success(request, f'取引先「{client_name}」を削除しました。')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 関連するプロジェクト数
        context['related_projects_count'] = ProjectDetail.objects.filter(
            billing_destination=self.object.client_name
        ).count()
        
        return context