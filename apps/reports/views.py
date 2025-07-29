# 標準ライブラリ
import os
import json
import io
import calendar
from datetime import date, datetime, timedelta

# サードパーティライブラリ
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Django
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import get_user_model

# ローカルアプリ
from .models import ReportExport, WorkloadAggregation
from .forms import WorkloadAggregationForm, WorkloadAggregationFilterForm
from apps.users.models import Department, Section
from apps.projects.models import ProjectTicket


User = get_user_model()

class WorkloadAggregationListView(LoginRequiredMixin, ListView):
    """工数集計一覧画面（工数集計レポート機能）"""
    model = WorkloadAggregation
    template_name = 'reports/workload_aggregation.html'
    context_object_name = 'aggregated_projects'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = WorkloadAggregation.objects.select_related(
            'case_name', 'section', 'mub_manager', 'created_by'
        ).order_by('-order_date', '-created_at')
        
        # フィルター処理
        form = WorkloadAggregationFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('project_name'):
                queryset = queryset.filter(project_name__icontains=form.cleaned_data['project_name'])
            if form.cleaned_data.get('case_name'):
                queryset = queryset.filter(case_name=form.cleaned_data['case_name'])
            if form.cleaned_data.get('section'):
                queryset = queryset.filter(section=form.cleaned_data['section'])
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('case_classification'):
                queryset = queryset.filter(case_classification=form.cleaned_data['case_classification'])
            if form.cleaned_data.get('mub_manager'):
                queryset = queryset.filter(mub_manager=form.cleaned_data['mub_manager'])
            if form.cleaned_data.get('search'):
                search_term = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(project_name__icontains=search_term) |
                    Q(case_name__name__icontains=search_term) |
                    Q(remarks__icontains=search_term)
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # フィルターフォーム
        context['filter_form'] = WorkloadAggregationFilterForm(self.request.GET)
        
        # 統計データ
        queryset = self.get_queryset()
        context['total_stats'] = {
            'total_available_amount': queryset.aggregate(total=Sum('available_amount'))['total'] or 0,
            'total_billing_amount': queryset.aggregate(total=Sum('billing_amount_excluding_tax'))['total'] or 0,
            'total_outsourcing': queryset.aggregate(total=Sum('outsourcing_cost_excluding_tax'))['total'] or 0,
            'total_estimated_workdays': queryset.aggregate(total=Sum('estimated_workdays'))['total'] or 0,
            'total_used_workdays': queryset.aggregate(total=Sum('used_workdays'))['total'] or 0,
            'total_newbie_workdays': queryset.aggregate(total=Sum('newbie_workdays'))['total'] or 0,
        }
        
        # 現在のフィルター値
        context['current_filters'] = {
            'project_name': self.request.GET.get('project_name', ''),
            'case_name_id': self.request.GET.get('case_name', ''),
            'section_id': self.request.GET.get('section', ''),
            'status': self.request.GET.get('status', ''),
            'case_classification': self.request.GET.get('case_classification', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        return context

class WorkloadAggregationCreateView(LoginRequiredMixin, CreateView):
    """工数集計作成画面"""
    model = WorkloadAggregation
    form_class = WorkloadAggregationForm
    template_name = 'reports/workload_aggregation_form.html'
    success_url = reverse_lazy('reports:workload_aggregation')
    
    def get_initial(self):
        """フォームの初期値を設定"""
        initial = super().get_initial()
        initial.update({
            'unit_cost_per_month': 75.0,      # 単価のデフォルト値
            'billing_unit_cost_per_month': 90.0,  # 請求単価のデフォルト値
        })
        return initial
    
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
        context['title'] = '工数集計登録'
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '工数集計編集'
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
        'プロジェクト名', '案件名', '部名', 'ステータス', '案件分類', '見積日', '受注日',
        '終了日（予定）', '終了日実績', '検収日', '使用可能金額（税別）', '請求金額（税別）',
        '外注費（税別）', '見積工数（人日）', '使用工数（人日）', '新入社員使用工数（人日）',
        '使用工数合計', '残工数', '残金額', '利益率', '仕掛中金額', '請求先', 'MUB担当者', '作成日時'
    ])
    
    # フィルター適用
    queryset = WorkloadAggregation.objects.select_related(
        'case_name', 'section', 'mub_manager'
    ).order_by('-order_date')
    
    # URLパラメータでフィルター
    if request.GET.get('project_name'):
        queryset = queryset.filter(project_name__icontains=request.GET['project_name'])
    if request.GET.get('case_name'):
        queryset = queryset.filter(case_name_id=request.GET['case_name'])
    if request.GET.get('status'):
        queryset = queryset.filter(status=request.GET['status'])
    
    for workload in queryset:
        writer.writerow([
            workload.project_name,
            workload.case_name.name,
            workload.section.name,
            workload.get_status_display(),
            workload.get_case_classification_display(),
            workload.estimate_date.strftime('%Y-%m-%d') if workload.estimate_date else '',
            workload.order_date.strftime('%Y-%m-%d') if workload.order_date else '',
            workload.planned_end_date.strftime('%Y-%m-%d') if workload.planned_end_date else '',
            workload.actual_end_date.strftime('%Y-%m-%d') if workload.actual_end_date else '',
            workload.inspection_date.strftime('%Y-%m-%d') if workload.inspection_date else '',
            str(workload.available_amount),
            str(workload.billing_amount_excluding_tax),
            str(workload.outsourcing_cost_excluding_tax),
            str(workload.estimated_workdays),
            str(workload.used_workdays),
            str(workload.newbie_workdays),
            str(workload.total_used_workdays),
            str(workload.remaining_workdays),
            str(workload.remaining_amount),
            str(workload.profit_rate),
            str(workload.wip_amount),
            workload.billing_destination,
            workload.mub_manager.get_full_name() if workload.mub_manager else '',
            workload.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response

class ReportListView(LoginRequiredMixin, TemplateView):
    """レポート一覧画面"""
    template_name = 'reports/report_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # レポートメニューの定義
        reports = [
            {
                'name': '工数集計',
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
    """エクスポート履歴一覧表示"""
    model = ReportExport
    template_name = 'reports/report_export_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        """ユーザー別のエクスポート履歴を取得"""
        queryset = ReportExport.objects.select_related('requested_by').order_by('-requested_at')
        
        # 一般ユーザーは自分のエクスポートのみ表示
        if not self.request.user.is_staff:
            queryset = queryset.filter(requested_by=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'エクスポート履歴'
        return context
    
class ReportExportCreateView(LoginRequiredMixin, CreateView):
    """レポートエクスポート作成画面"""
    model = ReportExport
    template_name = 'reports/report_export_create.html'
    fields = ['export_type', 'export_format', 'description']
    success_url = reverse_lazy('reports:report_export_list')
    
    def form_valid(self, form):
        """フォーム検証成功時の処理"""
        obj = form.save(commit=False)
        obj.requested_by = self.request.user
        
        # ファイル名の生成
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        export_type_name = obj.get_export_type_display().replace(' ', '_').replace('レポート', '')
        format_ext = {
            'excel': 'xlsx',
            'csv': 'csv', 
            'pdf': 'pdf'
        }.get(obj.export_format, 'xlsx')
        
        obj.file_name = f"{export_type_name}_{timestamp}.{format_ext}"
        
        # 有効期限設定（7日後）
        obj.expires_at = timezone.now() + timedelta(days=7)
        
        # リクエストパラメータを保存
        obj.filter_conditions = dict(self.request.GET)
        
        obj.save()
        
        # バックグラウンドでエクスポート処理を実行
        self.start_export_process(obj)
        
        messages.success(
            self.request, 
            f'エクスポートリクエストを受け付けました。処理が完了するとダウンロード可能になります。'
        )
        
        return super().form_valid(form)
    
    def start_export_process(self, export_obj):
        """エクスポート処理を開始"""
        try:
            export_obj.status = ReportExport.StatusChoices.PROCESSING
            export_obj.started_at = timezone.now()
            export_obj.save()
            
            # エクスポート処理を実行
            if export_obj.export_type == ReportExport.ExportTypeChoices.WORKLOAD_AGGREGATION:
                self.export_workload_aggregation(export_obj)
            elif export_obj.export_type == ReportExport.ExportTypeChoices.WORKLOAD_DETAIL:
                self.export_workload_detail(export_obj)
            elif export_obj.export_type == ReportExport.ExportTypeChoices.PROJECT_SUMMARY:
                self.export_project_summary(export_obj)
            elif export_obj.export_type == ReportExport.ExportTypeChoices.USER_WORKLOAD:
                self.export_user_workload(export_obj)
            
            export_obj.status = ReportExport.StatusChoices.COMPLETED
            export_obj.completed_at = timezone.now()
            export_obj.save()
            
        except Exception as e:
            export_obj.status = ReportExport.StatusChoices.FAILED
            export_obj.error_message = str(e)
            export_obj.completed_at = timezone.now()
            export_obj.save()
    
    def export_workload_aggregation(self, export_obj):
        """工数集計レポートのエクスポート"""
        # データ取得
        queryset = WorkloadAggregation.objects.select_related(
            'project_name', 'case_name', 'section', 'mub_manager'
        ).order_by('-order_date')
        
        # フィルター適用
        filters = export_obj.filter_conditions
        if filters.get('project_name'):
            queryset = queryset.filter(project_name_id__in=filters['project_name'])
        if filters.get('case_name'):
            queryset = queryset.filter(case_name_id__in=filters['case_name'])
        if filters.get('status'):
            queryset = queryset.filter(status__in=filters['status'])
        if filters.get('case_classification'):
            queryset = queryset.filter(case_classification__in=filters['case_classification'])
        
        export_obj.total_records = queryset.count()
        export_obj.save()
        
        # エクスポート形式に応じて処理
        if export_obj.export_format == ReportExport.ExportFormatChoices.EXCEL:
            file_path = self.create_excel_workload_aggregation(export_obj, queryset)
        elif export_obj.export_format == ReportExport.ExportFormatChoices.CSV:
            file_path = self.create_csv_workload_aggregation(export_obj, queryset)
        elif export_obj.export_format == ReportExport.ExportFormatChoices.PDF:
            file_path = self.create_pdf_workload_aggregation(export_obj, queryset)
        
        # ファイルサイズとパスを保存
        if os.path.exists(file_path):
            export_obj.file_path = file_path
            export_obj.file_size = os.path.getsize(file_path)
            export_obj.exported_records = queryset.count()
        
        export_obj.save()
    
    def create_excel_workload_aggregation(self, export_obj, queryset):
        """Excel形式で工数集計レポートを作成"""
        # エクスポートディレクトリの作成
        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        file_path = os.path.join(export_dir, export_obj.file_name)
        
        # Excelワークブック作成
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "工数集計レポート"
        
        # ヘッダースタイル
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # ヘッダー行
        headers = [
            'プロジェクト名', '案件名', '部名', 'ステータス', '案件分類',
            '見積日', '受注日', '終了日（予定）', '終了日実績', '検収日',
            '使用可能金額（税別）', '請求金額（税別）', '外注費（税別）',
            '見積工数（人日）', '使用工数（人日）', '新入社員使用工数（人日）',
            '単価（万円/月）', '請求単価（万円/月）',
            '請求先', 'MUB担当者', '備考', '作成日時'
        ]
        
        # ヘッダー設定
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # データ行
        for row_num, workload in enumerate(queryset, 2):
            try:
                # 安全なデータ取得
                data_row = [
                    str(workload.project_name) if workload.project_name else '',
                    str(workload.case_name.title) if workload.case_name else '',
                    str(workload.section.name) if workload.section else '',
                    str(workload.get_status_display()),
                    str(workload.get_case_classification_display()),
                    workload.estimate_date.strftime('%Y-%m-%d') if workload.estimate_date else '',
                    workload.order_date.strftime('%Y-%m-%d') if workload.order_date else '',
                    workload.planned_end_date.strftime('%Y-%m-%d') if workload.planned_end_date else '',
                    workload.actual_end_date.strftime('%Y-%m-%d') if workload.actual_end_date else '',
                    workload.inspection_date.strftime('%Y-%m-%d') if workload.inspection_date else '',
                    float(workload.available_amount or 0),
                    float(workload.billing_amount_excluding_tax or 0),
                    float(workload.outsourcing_cost_excluding_tax or 0),
                    float(workload.estimated_workdays or 0),
                    float(workload.used_workdays or 0),
                    float(workload.newbie_workdays or 0),
                    float(workload.unit_cost_per_month or 0),
                    float(workload.billing_unit_cost_per_month or 0),
                    str(workload.billing_destination) if workload.billing_destination else '',
                    str(workload.mub_manager.get_full_name()) if workload.mub_manager else '',
                    str(workload.remarks) if workload.remarks else '',
                    workload.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                ]
                
                for col_num, value in enumerate(data_row, 1):
                    ws.cell(row=row_num, column=col_num, value=value)
        
            except Exception as e:
                print(f"Excel row error: {str(e)}")
                continue
        
        # 列幅の自動調整
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # ファイルに保存
        wb.save(file_path)
        
        # ファイルパスを返す（HTTPレスポンスではない）
        return file_path

    def create_csv_workload_aggregation(self, export_obj, queryset):
        """CSV形式で工数集計レポートを作成"""
        # エクスポートディレクトリの作成
        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        file_path = os.path.join(export_dir, export_obj.file_name)
        
        # CSVファイルに書き込み
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # ヘッダー行
            writer.writerow([
                'プロジェクト名', '案件名', '部名', 'ステータス', '案件分類',
                '見積日', '受注日', '終了日（予定）', '終了日実績', '検収日',
                '使用可能金額（税別）', '請求金額（税別）', '外注費（税別）',
                '見積工数（人日）', '使用工数（人日）', '新入社員使用工数（人日）',
                '単価（万円/月）', '請求単価（万円/月）',
                '請求先', 'MUB担当者', '備考', '作成日時'
            ])
            
            # データ行
            for workload in queryset:
                try:
                    writer.writerow([
                        str(workload.project_name) if workload.project_name else '',
                        str(workload.case_name.title) if workload.case_name else '',
                        str(workload.section.name) if workload.section else '',
                        str(workload.get_status_display()),
                        str(workload.get_case_classification_display()),
                        workload.estimate_date.strftime('%Y-%m-%d') if workload.estimate_date else '',
                        workload.order_date.strftime('%Y-%m-%d') if workload.order_date else '',
                        workload.planned_end_date.strftime('%Y-%m-%d') if workload.planned_end_date else '',
                        workload.actual_end_date.strftime('%Y-%m-%d') if workload.actual_end_date else '',
                        workload.inspection_date.strftime('%Y-%m-%d') if workload.inspection_date else '',
                        str(workload.available_amount or 0),
                        str(workload.billing_amount_excluding_tax or 0),
                        str(workload.outsourcing_cost_excluding_tax or 0),
                        str(workload.estimated_workdays or 0),
                        str(workload.used_workdays or 0),
                        str(workload.newbie_workdays or 0),
                        str(workload.unit_cost_per_month or 0),
                        str(workload.billing_unit_cost_per_month or 0),
                        str(workload.billing_destination) if workload.billing_destination else '',
                        str(workload.mub_manager.get_full_name()) if workload.mub_manager else '',
                        str(workload.remarks) if workload.remarks else '',
                        workload.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    ])
                except Exception as e:
                    print(f"CSV row error: {str(e)}")
                    continue
        
        # ファイルパスを返す
        return file_path

    def create_pdf_workload_aggregation(self, export_obj, queryset):
        """PDF形式で工数集計レポートを作成"""
        try:
            import traceback
            print("PDF export started...")
            
            # PDFレスポンスを作成
            response = HttpResponse(content_type='application/pdf')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'workload_report_{timestamp}.pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            print("Response created...")
            
            # PDFドキュメントを作成（簡素化）
            doc = SimpleDocTemplate(
                response,
                pagesize=A4,  # 横向きを縦向きに変更
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            print("Document template created...")
            
            # スタイルを作成（日本語フォント不使用）
            styles = getSampleStyleSheet()
            
            print("Styles created...")
            
            # PDFコンテンツを構築
            story = []
            
            # タイトル（英語で簡素化）
            title = Paragraph('Workload Aggregation Report', styles['Title'])
            story.append(title)
            
            # 出力日時（英語で簡素化）
            export_info = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(export_info, styles['Normal']))
            story.append(Spacer(1, 10*mm))
            
            print("Title and info added...")
            
            # データが存在しない場合
            if not queryset.exists():
                no_data_text = Paragraph('No data available.', styles['Normal'])
                story.append(no_data_text)
                doc.build(story)
                print("No data PDF created")
                return response
            
            # 簡単なテーブルデータを準備
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            
            headers = ['Project', 'Case', 'Status', 'Amount']
            
            # データ行を作成（最初の5件のみ）
            table_data = [headers]
            
            for i, workload in enumerate(queryset[:5]):
                try:
                    project_name = str(workload.project_name)[:20] if workload.project_name else 'N/A'
                    case_name = str(workload.case_name.title)[:20] if workload.case_name else 'N/A'
                    status = str(workload.get_status_display())
                    amount = f'{int(workload.billing_amount_excluding_tax or 0):,}'
                    
                    row = [project_name, case_name, status, amount]
                    table_data.append(row)
                    print(f"Row {i+1} added: {project_name}")
                except Exception as e:
                    print(f"Row {i+1} error: {str(e)}")
                    continue
            
            # テーブルを作成
            table = Table(table_data, repeatRows=1)
            
            # シンプルなテーブルスタイル
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            
            table.setStyle(table_style)
            story.append(table)
            
            print(f"Table created with {len(table_data)} rows")
            
            # PDFを生成
            print("Building PDF...")
            doc.build(story)
            print("PDF built successfully")
            return response
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"PDF generation error: {str(e)}")
            print(f"Full traceback: {error_detail}")
            
            # エラー情報をテキストファイルとして返す
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            response = HttpResponse(content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="pdf_error_log_{timestamp}.txt"'
            response.write(f'PDF Generation Error Log\n')
            response.write(f'========================\n\n')
            response.write(f'Error: {str(e)}\n\n')
            response.write(f'Full Traceback:\n{error_detail}\n\n')
            response.write(f'QuerySet count: {queryset.count()}\n')
            response.write(f'First record: {queryset.first()}\n')
            return response

@login_required
def download_export(request, pk):
    """エクスポートファイルのダウンロード"""
    export_obj = get_object_or_404(ReportExport, pk=pk)
    
    # ダウンロード権限チェック
    if not export_obj.is_public and export_obj.requested_by != request.user:
        if not request.user.is_staff:
            messages.error(request, 'このファイルをダウンロードする権限がありません。')
            return redirect('reports:report_export_list')
    
    # ファイル存在チェック
    if not export_obj.is_downloadable:
        messages.error(request, 'ファイルがダウンロード可能な状態ではありません。')
        return redirect('reports:report_export_list')
    
    # 有効期限チェック
    if export_obj.is_expired:
        messages.error(request, 'ファイルの有効期限が切れています。')
        return redirect('reports:report_export_list')
    
    # ファイルの存在確認
    file_path = export_obj.file_path
    if not os.path.exists(file_path):
        messages.error(request, 'ファイルが見つかりません。')
        return redirect('reports:report_export_list')
    
    # ダウンロード回数を増加
    export_obj.increment_download_count()
    
    # ファイルダウンロード
    try:
        with open(file_path, 'rb') as file:
            response = HttpResponse(
                file.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{export_obj.file_name}"'
            return response
    except Exception as e:
        messages.error(request, f'ファイルのダウンロード中にエラーが発生しました: {str(e)}')
        return redirect('reports:report_export_list')

@login_required
@require_http_methods(["POST"])
def calculate_workdays_api(request):
    """工数自動計算API（Workloadモデル対応版）"""
    try:
        data = json.loads(request.body)
        case_id = data.get('case_id')  # これはProjectTicketのID
        order_date = data.get('order_date')
        actual_end_date = data.get('actual_end_date')
        
        if not case_id:
            return JsonResponse({'success': False, 'error': 'チケットIDが必要です。'})
        
        from apps.workloads.models import Workload
        from decimal import Decimal
        
        # 工数データの取得（Workloadモデル）
        workloads_query = Workload.objects.filter(ticket__id=case_id)
        
        # 日付フィルター適用（年月ベースで）
        target_year_months = set()
        
        if order_date:
            start_date = datetime.strptime(order_date, '%Y-%m-%d').date()
        else:
            # デフォルトは現在年月から6ヶ月前
            start_date = date.today().replace(day=1)
        
        if actual_end_date:
            end_date = datetime.strptime(actual_end_date, '%Y-%m-%d').date()
        else:
            # デフォルトは現在年月
            end_date = date.today()
        
        # 対象年月のリストを作成
        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            target_year_months.add(current_date.strftime('%Y-%m'))
            # 次の月へ
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # 対象年月でフィルター
        if target_year_months:
            workloads_query = workloads_query.filter(year_month__in=target_year_months)
        
        # 一般使用工数と新入社員工数を分離
        regular_workdays = Decimal('0.0')
        newbie_workdays = Decimal('0.0')
        
        for workload in workloads_query:
            # ユーザーのemployee_levelを確認
            is_junior = False
            if hasattr(workload.user, 'employee_level') and workload.user.employee_level == 'junior':
                is_junior = True
            
            # 各日の工数を合計（日付範囲内のみ）
            workload_year_month = workload.year_month
            year, month = map(int, workload_year_month.split('-'))
            
            # その月の日数を取得
            days_in_month = calendar.monthrange(year, month)[1]
            
            for day in range(1, days_in_month + 1):
                # 日付範囲チェック
                current_day = date(year, month, day)
                if order_date:
                    start_check = datetime.strptime(order_date, '%Y-%m-%d').date()
                    if current_day < start_check:
                        continue
                if actual_end_date:
                    end_check = datetime.strptime(actual_end_date, '%Y-%m-%d').date()
                    if current_day > end_check:
                        continue
                
                # その日の工数を取得
                day_hours = workload.get_day_value(day)
                
                # 工数の分類
                if is_junior:
                    newbie_workdays += Decimal(str(day_hours))
                else:
                    regular_workdays += Decimal(str(day_hours))
        
        # 時間を人日に変換（8時間=1人日として計算）
        used_workdays = regular_workdays / 8
        newbie_workdays_converted = newbie_workdays / 8
        
        return JsonResponse({
            'success': True,
            'used_workdays': float(used_workdays),
            'newbie_workdays': float(newbie_workdays_converted),
            'total_workdays': float(used_workdays + newbie_workdays_converted),
            'ticket_name': ticket.title,
            'debug_info': {
                'workload_records': workloads_query.count(),
                'target_months': list(target_year_months),
                'regular_hours': float(regular_workdays),
                'newbie_hours': float(newbie_workdays)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'サーバーエラー: {str(e)}'
        })

@login_required
@require_POST
def calculate_workdays_ajax(request):
    """AJAX工数計算エンドポイント"""
    try:
        ticket_id = request.POST.get('ticket_id')
        classification = request.POST.get('classification', 'development')
        
        if not ticket_id:
            return JsonResponse({
                'success': False,
                'error': 'チケットIDが指定されていません'
            })
        
        # チケットを取得
        try:
            ticket = ProjectTicket.objects.get(id=ticket_id, is_active=True)
        except ProjectTicket.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '指定されたチケットが見つかりません'
            })
        
        # 一時的な工数集計インスタンスを作成
        temp_aggregation = WorkloadAggregation()
        temp_aggregation.case_name = ticket
        temp_aggregation.case_classification = classification
        
        # 工数計算実行
        result = temp_aggregation.calculate_workdays_from_workload()
        
        return JsonResponse({
            'success': True,
            'used_workdays': float(result['used_workdays']),
            'newbie_workdays': float(result['newbie_workdays']),
            'total_workdays': float(result['total_workdays']),
            'debug_info': result['debug_info']
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"AJAX工数計算エラー: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'error': f'計算エラー: {str(e)}'
        })

@login_required
def workload_export_current(request):
    """現在表示中の工数集計データをエクスポート"""
    if request.method != 'POST':
        return redirect('reports:workload_aggregation')
    
    # フィルター条件を取得（フォームデータまたはGETパラメータから）
    filters = {}
    for key in ['project_name', 'case_name', 'status', 'case_classification', 'section', 'mub_manager']:
        value = request.POST.get(key) or request.GET.get(key)
        if value:
            filters[key] = value
    
    # データセットを取得（一覧画面と同じロジック）
    queryset = WorkloadAggregation.objects.select_related(
        'case_name', 'section', 'mub_manager'
    )
    
    # フィルター適用
    if filters.get('project_name'):
        queryset = queryset.filter(project_name__icontains=filters['project_name'])
    if filters.get('case_name'):
        queryset = queryset.filter(case_name_id=filters['case_name'])
    if filters.get('status'):
        queryset = queryset.filter(status=filters['status'])
    if filters.get('case_classification'):
        queryset = queryset.filter(case_classification=filters['case_classification'])
    if filters.get('section'):
        queryset = queryset.filter(section_id=filters['section'])
    if filters.get('mub_manager'):
        queryset = queryset.filter(mub_manager_id=filters['mub_manager'])
    
    # 並び順（一覧画面と同じ）
    queryset = queryset.order_by('-created_at')
    
    # エクスポート形式を取得
    export_format = request.POST.get('format', 'excel')
    
    # エクスポート実行
    if export_format == 'excel':
        print("Processing EXCEL export...")
        return export_workload_excel(queryset, export_type='excel')
    elif export_format == 'csv':
        print("Processing CSV export...")
        return export_workload_csv(queryset)
    elif export_format == 'pdf':
        print("Processing PDF export...")
        # PDF専用のシンプルな処理
        try:
            return export_workload_pdf_simple(queryset, filters)
        except Exception as e:
            print(f"PDF export failed: {str(e)}")
            # CSVで代替
            print("Falling back to CSV...")
            messages.warning(request, 'PDF生成に失敗したため、CSVファイルをダウンロードします。')
            return export_workload_csv(queryset)
    else:
        print(f"Unknown format: {export_format}")
        messages.error(request, f'サポートされていない形式です: {export_format}')
        return redirect('reports:workload_aggregation')

def export_workload_pdf_simple(queryset, filters=None):
    """最もシンプルなPDF生成"""
    try:
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        print("Starting simple PDF generation...")
        
        buffer = BytesIO()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # canvasで直接PDF作成（最も基本的な方法）
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        print("Canvas created...")
        
        # タイトル
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Workload Report")
        
        # 日付
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # データを列挙（最大10件）
        y_position = height - 120
        p.setFont("Helvetica", 8)
        
        print(f"Processing {queryset.count()} records...")
        
        for i, workload in enumerate(queryset[:10]):
            if y_position < 50:  # ページの下端に達したら停止
                break
            try:
                project_name = str(workload.project_name)[:40] if workload.project_name else 'N/A'
                case_title = str(workload.case_name.title)[:40] if workload.case_name else 'N/A'
                line = f"{i+1}. {project_name} | {case_title}"
                p.drawString(50, y_position, line)
                y_position -= 15
                print(f"Added line {i+1}: {project_name}")
            except Exception as e:
                print(f"Error processing record {i+1}: {str(e)}")
                p.drawString(50, y_position, f"{i+1}. [Error processing record]")
                y_position -= 15
        
        # 統計情報
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y_position - 20, f"Total Records: {queryset.count()}")
        
        print("Saving PDF...")
        p.showPage()
        p.save()
        
        # レスポンス作成
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        filename = f"workload_simple_{timestamp}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"PDF created successfully: {filename}")
        return response
        
    except Exception as e:
        print(f"Simple PDF creation failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e

def export_workload_pdf_enhanced(queryset, filters=None):
    """拡張版PDF生成"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        from io import BytesIO
        
        print("Starting enhanced PDF generation...")
        
        buffer = BytesIO()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 横向きA4でより多くの情報を表示
        p = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)
        
        # タイトル
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "工数集計レポート (Workload Aggregation Report)")
        
        # 日付とフィルター情報
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        p.drawString(50, height - 100, f"総件数: {queryset.count()}件")
        
        # ヘッダー行
        p.setFont("Helvetica-Bold", 8)
        y_position = height - 130
        headers = ["No", "プロジェクト名", "案件名", "ステータス", "請求金額", "使用工数"]
        x_positions = [50, 100, 250, 400, 500, 600]
        
        for i, header in enumerate(headers):
            p.drawString(x_positions[i], y_position, header)
        
        # 線を引く
        p.line(50, y_position - 5, width - 50, y_position - 5)
        
        # データ行
        p.setFont("Helvetica", 7)
        y_position -= 20
        
        for i, workload in enumerate(queryset[:25]):  # 25件まで表示
            if y_position < 50:  # ページ下端チェック
                p.showPage()  # 新しいページ
                y_position = height - 50
                # ヘッダーを再描画
                p.setFont("Helvetica-Bold", 8)
                for j, header in enumerate(headers):
                    p.drawString(x_positions[j], y_position, header)
                p.line(50, y_position - 5, width - 50, y_position - 5)
                p.setFont("Helvetica", 7)
                y_position -= 20
            
            try:
                # データを準備
                project_name = str(workload.project_name)[:20] if workload.project_name else 'N/A'
                case_title = str(workload.case_name.title)[:25] if workload.case_name else 'N/A'
                status = str(workload.get_status_display())[:15] if hasattr(workload, 'get_status_display') else 'N/A'
                billing = f"¥{int(workload.billing_amount_excluding_tax or 0):,}"
                workdays = f"{float(workload.used_workdays or 0):.1f}日"
                
                # データを描画
                data = [str(i+1), project_name, case_title, status, billing, workdays]
                for j, value in enumerate(data):
                    p.drawString(x_positions[j], y_position, value)
                
                y_position -= 15
                
            except Exception as e:
                print(f"Error processing record {i+1}: {str(e)}")
                p.drawString(50, y_position, f"{i+1}. [データ処理エラー]")
                y_position -= 15
        
        # 統計情報
        y_position -= 20
        p.setFont("Helvetica-Bold", 10)
        
        # 統計計算
        total_billing = sum(float(w.billing_amount_excluding_tax or 0) for w in queryset)
        total_workdays = sum(float(w.used_workdays or 0) for w in queryset)
        
        stats_text = [
            f"総請求金額: ¥{total_billing:,.0f}",
            f"総使用工数: {total_workdays:.1f}人日",
            f"平均単価: ¥{(total_billing/total_workdays):,.0f}/人日" if total_workdays > 0 else "平均単価: N/A"
        ]
        
        for stat in stats_text:
            p.drawString(50, y_position, stat)
            y_position -= 20
        
        print("Saving enhanced PDF...")
        p.showPage()
        p.save()
        
        # レスポンス作成
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        filename = f"workload_enhanced_{timestamp}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"Enhanced PDF created successfully: {filename}")
        return response
        
    except Exception as e:
        print(f"Enhanced PDF creation failed: {str(e)}")
        # シンプル版にフォールバック
        return export_workload_pdf_simple(queryset, filters)

def export_workload_text_fallback(queryset, filters=None):
    """最終手段：テキストファイル"""
    print("Creating text fallback...")
    
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'workload_text_{timestamp}.txt'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    response.write(f'Workload Report (Text Format)\n')
    response.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    response.write(f'Total Records: {queryset.count()}\n\n')
    
    for i, workload in enumerate(queryset[:50], 1):
        try:
            project_name = str(workload.project_name) if workload.project_name else 'N/A'
            case_title = str(workload.case_name.title) if workload.case_name else 'N/A'
            status = str(workload.get_status_display()) if hasattr(workload, 'get_status_display') else 'N/A'
            amount = str(workload.billing_amount_excluding_tax or 0)
            
            response.write(f'{i}. {project_name} | {case_title} | {status} | ¥{amount}\n')
        except Exception as e:
            response.write(f'{i}. [Error processing record: {str(e)}]\n')
    
    print(f"Text file created: {filename}")
    return response

def export_workload_excel(queryset, export_type='excel'):
    """Excel形式でエクスポート"""
    # Excelワークブック作成
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "工数集計レポート"
    
    # ヘッダースタイル
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # ヘッダー行
    headers = [
        'プロジェクト名', '案件名', '部名', 'ステータス', '案件分類',
        '見積日', '受注日', '終了日（予定）', '終了日実績', '検収日',
        '使用可能金額（税別）', '請求金額（税別）', '外注費（税別）',
        '見積工数（人日）', '使用工数（人日）', '新入社員使用工数（人日）',
        '単価（万円/月）', '請求単価（万円/月）',
        '請求先', 'MUB担当者', '備考', '作成日時'
    ]
    
    # ヘッダー設定
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # データ行
    for row_num, workload in enumerate(queryset, 2):
        try:
            data_row = [
                str(workload.project_name) if workload.project_name else '',
                str(workload.case_name.title) if workload.case_name else '',
                str(workload.section.name) if workload.section else '',
                str(workload.get_status_display()),
                str(workload.get_case_classification_display()),
                workload.estimate_date.strftime('%Y-%m-%d') if workload.estimate_date else '',
                workload.order_date.strftime('%Y-%m-%d') if workload.order_date else '',
                workload.planned_end_date.strftime('%Y-%m-%d') if workload.planned_end_date else '',
                workload.actual_end_date.strftime('%Y-%m-%d') if workload.actual_end_date else '',
                workload.inspection_date.strftime('%Y-%m-%d') if workload.inspection_date else '',
                float(workload.available_amount or 0),
                float(workload.billing_amount_excluding_tax or 0),
                float(workload.outsourcing_cost_excluding_tax or 0),
                float(workload.estimated_workdays or 0),
                float(workload.used_workdays or 0),
                float(workload.newbie_workdays or 0),
                float(workload.unit_cost_per_month or 0),
                float(workload.billing_unit_cost_per_month or 0),
                workload.billing_destination or '',
                workload.mub_manager.get_full_name() if workload.mub_manager else '',
                workload.remarks or '',
                workload.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            ]
            
            for col_num, value in enumerate(data_row, 1):
                ws.cell(row=row_num, column=col_num, value=value)
        except Exception as e:
            # エラーが発生した行をスキップ
            print(f"Row {row_num} export error: {str(e)}")
            continue
    
    # 列幅の自動調整
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # HTTPレスポンスとして返却
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # シンプルな英語ファイル名
    if export_type == 'pdf':
        filename = f'workload_extended_{timestamp}.xlsx'
    else:
        filename = f'workload_standard_{timestamp}.xlsx'
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def export_workload_csv(queryset):
    """CSV形式でエクスポート"""
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    
    # ヘッダー行
    writer.writerow([
        'プロジェクト名', '案件名', '部名', 'ステータス', '案件分類',
        '見積日', '受注日', '終了日（予定）', '終了日実績', '検収日',
        '使用可能金額（税別）', '請求金額（税別）', '外注費（税別）',
        '見積工数（人日）', '使用工数（人日）', '新入社員使用工数（人日）',
        '単価（万円/月）', '請求単価（万円/月）',
        '請求先', 'MUB担当者', '備考', '作成日時'
    ])
    
    # データ行
    for workload in queryset:
        try:
            writer.writerow([
                str(workload.project_name) if workload.project_name else '',
                str(workload.case_name.title) if workload.case_name else '',
                str(workload.section.name) if workload.section else '',
                str(workload.get_status_display()),
                str(workload.get_case_classification_display()),
                workload.estimate_date.strftime('%Y-%m-%d') if workload.estimate_date else '',
                workload.order_date.strftime('%Y-%m-%d') if workload.order_date else '',
                workload.planned_end_date.strftime('%Y-%m-%d') if workload.planned_end_date else '',
                workload.actual_end_date.strftime('%Y-%m-%d') if workload.actual_end_date else '',
                workload.inspection_date.strftime('%Y-%m-%d') if workload.inspection_date else '',
                str(workload.available_amount or 0),
                str(workload.billing_amount_excluding_tax or 0),
                str(workload.outsourcing_cost_excluding_tax or 0),
                str(workload.estimated_workdays or 0),
                str(workload.used_workdays or 0),
                str(workload.newbie_workdays or 0),
                str(workload.unit_cost_per_month or 0),
                str(workload.billing_unit_cost_per_month or 0),
                str(workload.billing_destination) if workload.billing_destination else '',
                str(workload.mub_manager.get_full_name()) if workload.mub_manager else '',
                str(workload.remarks) if workload.remarks else '',
                workload.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
        except Exception as e:
            # エラーが発生した行をスキップ
            print(f"CSV export error: {str(e)}")
            continue
    
    # HTTPレスポンスとして返却（拡張子は.csv）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'workload_csv_{timestamp}.csv'
    
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def export_workload_pdf(queryset, filters=None):
    """PDF形式でエクスポート（デバッグ版）"""
    try:
        import traceback
        print("PDF export started...")
        
        # PDFレスポンスを作成
        response = HttpResponse(content_type='application/pdf')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'workload_report_{timestamp}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print("Response created...")
        
        # PDFドキュメントを作成（簡素化）
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,  # 横向きを縦向きに変更
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        print("Document template created...")
        
        # スタイルを作成（日本語フォント不使用）
        styles = getSampleStyleSheet()
        
        print("Styles created...")
        
        # PDFコンテンツを構築
        story = []
        
        # タイトル（英語で簡素化）
        title = Paragraph('Workload Aggregation Report', styles['Title'])
        story.append(title)
        
        # 出力日時（英語で簡素化）
        export_info = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(export_info, styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        print("Title and info added...")
        
        # データが存在しない場合
        if not queryset.exists():
            no_data_text = Paragraph('No data available.', styles['Normal'])
            story.append(no_data_text)
            doc.build(story)
            print("No data PDF created")
            return response
        
        # 簡単なテーブルデータを準備
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        headers = ['Project', 'Case', 'Status', 'Amount']
        
        # データ行を作成（最初の5件のみ）
        table_data = [headers]
        
        for i, workload in enumerate(queryset[:5]):
            try:
                project_name = str(workload.project_name)[:20] if workload.project_name else 'N/A'
                case_name = str(workload.case_name.title)[:20] if workload.case_name else 'N/A'
                status = str(workload.get_status_display())
                amount = f'{int(workload.billing_amount_excluding_tax or 0):,}'
                
                row = [project_name, case_name, status, amount]
                table_data.append(row)
                print(f"Row {i+1} added: {project_name}")
            except Exception as e:
                print(f"Row {i+1} error: {str(e)}")
                continue
        
        # テーブルを作成
        table = Table(table_data, repeatRows=1)
        
        # シンプルなテーブルスタイル
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        table.setStyle(table_style)
        story.append(table)
        
        print(f"Table created with {len(table_data)} rows")
        
        # PDFを生成
        print("Building PDF...")
        doc.build(story)
        print("PDF built successfully")
        return response
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"PDF generation error: {str(e)}")
        print(f"Full traceback: {error_detail}")
        
        # エラー情報をテキストファイルとして返す
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="pdf_error_log_{timestamp}.txt"'
        response.write(f'PDF Generation Error Log\n')
        response.write(f'========================\n\n')
        response.write(f'Error: {str(e)}\n\n')
        response.write(f'Full Traceback:\n{error_detail}\n\n')
        response.write(f'QuerySet count: {queryset.count()}\n')
        response.write(f'First record: {queryset.first()}\n')
        return response

def export_workload_pdf_fallback(queryset, filters=None):
    """PDF形式でエクスポート（フォールバック版）"""
    try:
        import traceback
        print("Fallback PDF export started...")
        
        # PDFレスポンスを作成
        response = HttpResponse(content_type='application/pdf')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'workload_report_fallback_{timestamp}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print("Response created...")
        
        # PDFドキュメントを作成（簡素化）
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,  # 横向きを縦向きに変更
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        print("Document template created...")
        
        # スタイルを作成（日本語フォント不使用）
        styles = getSampleStyleSheet()
        
        print("Styles created...")
        
        # PDFコンテンツを構築
        story = []
        
        # タイトル（英語で簡素化）
        title = Paragraph('Workload Aggregation Report (Fallback)', styles['Title'])
        story.append(title)
        
        # 出力日時（英語で簡素化）
        export_info = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(export_info, styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        print("Title and info added...")
        
        # データが存在しない場合
        if not queryset.exists():
            no_data_text = Paragraph('No data available.', styles['Normal'])
            story.append(no_data_text)
            doc.build(story)
            print("No data PDF created")
            return response
        
        # 簡単なテーブルデータを準備
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        headers = ['Project', 'Case', 'Status', 'Amount']
        
        # データ行を作成（最初の5件のみ）
        table_data = [headers]
        
        for i, workload in enumerate(queryset[:5]):
            try:
                project_name = str(workload.project_name)[:20] if workload.project_name else 'N/A'
                case_name = str(workload.case_name.title)[:20] if workload.case_name else 'N/A'
                status = str(workload.get_status_display())
                amount = f'{int(workload.billing_amount_excluding_tax or 0):,}'
                
                row = [project_name, case_name, status, amount]
                table_data.append(row)
                print(f"Row {i+1} added: {project_name}")
            except Exception as e:
                print(f"Row {i+1} error: {str(e)}")
                continue
        
        # テーブルを作成
        table = Table(table_data, repeatRows=1)
        
        # シンプルなテーブルスタイル
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        table.setStyle(table_style)
        story.append(table)
        
        print(f"Table created with {len(table_data)} rows")
        
        # PDFを生成
        print("Building PDF...")
        doc.build(story)
        print("PDF built successfully")
        return response
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"PDF generation error: {str(e)}")
        print(f"Full traceback: {error_detail}")
        
        # エラー情報をテキストファイルとして返す
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="pdf_error_log_{timestamp}.txt"'
        response.write(f'PDF Generation Error Log\n')
        response.write(f'========================\n\n')
        response.write(f'Error: {str(e)}\n\n')
        response.write(f'Full Traceback:\n{error_detail}\n\n')
        response.write(f'QuerySet count: {queryset.count()}\n')
        response.write(f'First record: {queryset.first()}\n')
        return response