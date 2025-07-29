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
    path('workload-export/', views.workload_export, name='workload_export'),  # 既存（削除予定）
    path('workload-export-current/', views.workload_export_current, name='workload_export_current'),  # 新規

    # 新エクスポート機能（将来用）
    path('exports/', views.ReportExportListView.as_view(), name='report_export_list'),
    path('exports/create/', views.ReportExportCreateView.as_view(), name='report_export_create'),
    path('exports/<int:pk>/download/', views.download_export, name='download_export'),
    
    # 工数自動計算API
    path('api/calculate-workdays/', views.calculate_workdays_api, name='calculate_workdays_api'),
    
    # AJAX工数計算
    path('calculate-workdays/', views.calculate_workdays_ajax, name='calculate_workdays_ajax'),
]