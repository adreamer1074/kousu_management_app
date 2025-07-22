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
    path('workload-export/', views.workload_export, name='workload_export'),
    
    # レポートエクスポート関連
    path('exports/', views.ReportExportListView.as_view(), name='report_export_list'),
]