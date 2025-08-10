from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # レポート一覧（ルートパス）
    path('', views.ReportListView.as_view(), name='report_list'),
    
    # 工数集計レポート関連（工数集計一覧テーブル）
    path('workload-aggregation/', views.WorkloadAggregationListView.as_view(), name='workload_aggregation'),
    path('workload-aggregation/create/', views.WorkloadAggregationCreateView.as_view(), name='workload_aggregation_create'),
    path('workload-aggregation/<int:pk>/', views.WorkloadAggregationDetailView.as_view(), name='workload_aggregation_detail'),
    path('workload-aggregation/<int:pk>/edit/', views.WorkloadAggregationUpdateView.as_view(), name='workload_aggregation_edit'),
    path('workload-aggregation/<int:pk>/delete/', views.WorkloadAggregationDeleteView.as_view(), name='workload_aggregation_delete'),
    # エクスポート機能
    path('workload-export-current/', views.workload_export_current, name='workload_export_current'),  # 新規

    # エクスポート機能
    path('exports/', views.ReportExportListView.as_view(), name='report_export_list'), #未完了
    
    # 工数自動計算API(AJAX)
    path('calculate-workdays/', views.calculate_workdays_ajax, name='calculate_workdays_ajax'),

    # 工数一括更新用URL
    path('workload-aggregation/bulk-update-work-hours/', views.bulk_update_work_hours, name='bulk_update_work_hours'),
    
    # 外注費同期専用API
    path('workload-aggregation/sync-outsourcing-costs/', views.sync_outsourcing_costs, name='sync_outsourcing_costs'),
]