from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from django.db.models import Sum, Count, Q, F, Case, When, DecimalField
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
import json
import csv
from io import StringIO
from decimal import Decimal

from apps.workloads.models import Workload
from apps.projects.models import Project, ProjectDetail
from apps.users.models import CustomUser, Department
from apps.cost_master.models import CostMaster

@method_decorator(staff_member_required, name='dispatch')
class ReportListView(LoginRequiredMixin, TemplateView):
    """レポート一覧画面"""
    template_name = 'reports/report_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 利用可能なレポート一覧
        reports = [
            {
                'name': '工数集計レポート',
                'description': '月次工数の詳細集計と分析',
                'url': 'reports:workload_aggregation',
                'icon': 'bi-bar-chart-line',
                'color': 'primary',
            },
            {
                'name': 'プロジェクト別レポート',
                'description': 'プロジェクト単位での工数・費用分析',
                'url': 'reports:workload_aggregation',
                'icon': 'bi-folder-open',
                'color': 'info',
            },
        ]
        
        context['reports'] = reports
        return context

@method_decorator(staff_member_required, name='dispatch')
class WorkloadAggregationView(LoginRequiredMixin, TemplateView):
    """工数集計画面（管理者専用）"""
    template_name = 'reports/workload_aggregation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # フィルターパラメータ取得
        year_month = self.request.GET.get('year_month', self.get_current_month())
        project_id = self.request.GET.get('project_id')
        department_id = self.request.GET.get('department_id')
        status = self.request.GET.get('status')
        case_classification = self.request.GET.get('case_classification')
        search_query = self.request.GET.get('search')
        
        # 基本クエリセット（修正: workload_setをworkloadsに変更）
        queryset = ProjectDetail.objects.select_related(
            'project', 'department'
        ).prefetch_related(
            'project__workloads'  # workload_set → workloads に修正
        )
        
        # フィルター適用
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if status:
            queryset = queryset.filter(status=status)
        if case_classification:
            queryset = queryset.filter(case_classification=case_classification)
        if search_query:
            queryset = queryset.filter(
                Q(project_name__icontains=search_query) |
                Q(case_name__icontains=search_query) |
                Q(billing_destination__icontains=search_query) |
                Q(mub_manager__icontains=search_query)
            )
        
        # 各案件の工数データを更新
        aggregated_projects = []
        total_stats = {
            'total_budget': 0,
            'total_billing': 0,
            'total_outsourcing': 0,
            'total_estimated_workdays': 0,
            'total_used_workdays': 0,
            'total_newbie_workdays': 0,
            'total_wip_amount': 0,
        }
        
        for project_detail in queryset:
            # 指定年月の工数を集計（修正: workload_set → workloads）
            monthly_workloads = project_detail.project.workloads.filter(
                year_month=year_month
            )
            
            monthly_used_workdays = sum(w.total_days for w in monthly_workloads)
            monthly_newbie_workdays = sum(
                w.total_days for w in monthly_workloads 
                if w.user.date_joined and 
                (timezone.now() - w.user.date_joined).days < 365  # 新入社員判定
            )
            
            # 集計データを作成
            project_data = {
                'detail': project_detail,
                'monthly_used_workdays': monthly_used_workdays,
                'monthly_newbie_workdays': monthly_newbie_workdays,
                'monthly_remaining_workdays': project_detail.estimated_workdays - Decimal(str(monthly_used_workdays)),
                'monthly_wip_amount': self.calculate_wip_amount(project_detail, monthly_used_workdays),
                'monthly_remaining_amount': self.calculate_remaining_amount(project_detail, monthly_used_workdays),
                'profit_rate': project_detail.profit_rate,
            }
            
            aggregated_projects.append(project_data)
            
            # 合計統計に追加
            total_stats['total_budget'] += project_detail.budget_amount
            total_stats['total_billing'] += project_detail.billing_amount
            total_stats['total_outsourcing'] += project_detail.outsourcing_cost
            total_stats['total_estimated_workdays'] += project_detail.estimated_workdays
            total_stats['total_used_workdays'] += monthly_used_workdays
            total_stats['total_newbie_workdays'] += monthly_newbie_workdays
            total_stats['total_wip_amount'] += project_data['monthly_wip_amount']
        
        # フィルターオプション
        filter_options = {
            'projects': Project.objects.filter(is_active=True),
            'departments': Department.objects.filter(is_active=True),
            'statuses': ProjectDetail.STATUS_CHOICES,
            'classifications': ProjectDetail.CASE_CLASSIFICATION_CHOICES,
            'available_months': self.get_available_months(),
        }
        
        context.update({
            'year_month': year_month,
            'aggregated_projects': aggregated_projects,
            'total_stats': total_stats,
            'filter_options': filter_options,
            'current_filters': {
                'project_id': project_id,
                'department_id': department_id,
                'status': status,
                'case_classification': case_classification,
                'search': search_query,
            },
        })
        
        return context
    
    def get_current_month(self):
        """現在の年月を取得"""
        current = timezone.now()
        return f"{current.year}-{current.month:02d}"
    
    def get_available_months(self):
        """利用可能な年月一覧"""
        months = Workload.objects.values_list('year_month', flat=True).distinct().order_by('-year_month')
        return list(months)
    
    def calculate_wip_amount(self, project_detail, used_workdays):
        """仕掛中金額計算"""
        try:
            cost_master = CostMaster.objects.filter(
                department=project_detail.department,
                is_active=True
            ).first()
            if cost_master:
                return used_workdays * cost_master.daily_cost
        except:
            pass
        return 0
    
    def calculate_remaining_amount(self, project_detail, used_workdays):
        """残金額計算"""
        try:
            cost_master = CostMaster.objects.filter(
                department=project_detail.department,
                is_active=True
            ).first()
            if cost_master:
                used_cost = used_workdays * cost_master.daily_cost
                return project_detail.budget_amount - used_cost
        except:
            pass
        return project_detail.budget_amount

@method_decorator(staff_member_required, name='dispatch')
class WorkloadAggregationExportView(LoginRequiredMixin, TemplateView):
    """工数集計CSV出力"""
    
    def get(self, request, *args, **kwargs):
        year_month = request.GET.get('year_month')
        export_format = request.GET.get('format', 'csv')
        
        if not year_month:
            return JsonResponse({'error': '年月が指定されていません'}, status=400)
        
        # データ取得（フィルター適用）
        queryset = ProjectDetail.objects.select_related('project', 'department')
        
        # フィルター適用（WorkloadAggregationViewと同じロジック）
        project_id = request.GET.get('project_id')
        department_id = request.GET.get('department_id')
        status = request.GET.get('status')
        
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if status:
            queryset = queryset.filter(status=status)
        
        if export_format == 'csv':
            return self.export_csv(queryset, year_month)
        else:
            return JsonResponse({'error': '未対応の出力形式です'}, status=400)
    
    def export_csv(self, queryset, year_month):
        """CSV出力"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="workload_aggregation_{year_month}.csv"'
        
        # BOM付きCSV
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # ヘッダー行
        headers = [
            'プロジェクト名', '案件名', '部名', 'ステータス', '案件分類', '見積日', '受注日',
            '終了日（予定）', '終了日実績', '検収日', '使用可能金額（税別）', '請求金額（税別）',
            '外注費（税別）', '見積工数（人日）', '使用工数（人日）', '新入社員使用工数（人日）',
            '残工数（人日）', '残金額（税抜）', '利益率（%）', '仕掛中金額', '税込請求金額',
            '請求先', '請求先担当者', 'MUB担当者', '備考'
        ]
        writer.writerow(headers)
        
        # データ行
        for project_detail in queryset:
            # 月次工数計算
            monthly_workloads = Workload.objects.filter(
                project=project_detail.project,
                year_month=year_month
            )
            monthly_used_workdays = sum(w.total_days for w in monthly_workloads)
            monthly_newbie_workdays = sum(
                w.total_days for w in monthly_workloads 
                if w.user.date_joined and 
                (timezone.now() - w.user.date_joined).days < 365
            )
            
            row = [
                project_detail.project_name,
                project_detail.case_name,
                project_detail.department.name,
                project_detail.get_status_display(),
                project_detail.get_case_classification_display(),
                project_detail.estimate_date.strftime('%Y-%m-%d') if project_detail.estimate_date else '',
                project_detail.order_date.strftime('%Y-%m-%d') if project_detail.order_date else '',
                project_detail.planned_end_date.strftime('%Y-%m-%d') if project_detail.planned_end_date else '',
                project_detail.actual_end_date.strftime('%Y-%m-%d') if project_detail.actual_end_date else '',
                project_detail.inspection_date.strftime('%Y-%m-%d') if project_detail.inspection_date else '',
                float(project_detail.budget_amount),
                float(project_detail.billing_amount),
                float(project_detail.outsourcing_cost),
                float(project_detail.estimated_workdays),
                float(monthly_used_workdays),
                float(monthly_newbie_workdays),
                float(project_detail.estimated_workdays - monthly_used_workdays),
                float(project_detail.remaining_amount),
                f"{project_detail.profit_rate:.2f}",
                float(project_detail.wip_amount),
                float(project_detail.tax_included_billing_amount),
                project_detail.billing_destination,
                project_detail.billing_contact,
                project_detail.mub_manager,
                project_detail.remarks,
            ]
            writer.writerow(row)
        
        return response