from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # レポート一覧
    path('', views.ReportListView.as_view(), name='report_list'),
    
    # 工数集計レポート
    path('workload/', views.WorkloadAggregationView.as_view(), name='workload_aggregation'),
    path('workload/export/', views.WorkloadAggregationExportView.as_view(), name='workload_export'),
]