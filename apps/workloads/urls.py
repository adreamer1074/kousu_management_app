from django.urls import path
from . import views

app_name = 'workloads'

urlpatterns = [
    # 工数カレンダー
    path('', views.WorkloadCalendarView.as_view(), name='workload_calendar'),
    
    # 従来の工数管理ビュー（必要に応じて）
    path('list/', views.WorkloadListView.as_view(), name='workload_list'),
    path('create/', views.WorkloadCreateView.as_view(), name='workload_create'),
    path('<int:pk>/', views.WorkloadDetailView.as_view(), name='workload_detail'),
    path('<int:pk>/edit/', views.WorkloadUpdateView.as_view(), name='workload_edit'),
    path('<int:pk>/delete/', views.WorkloadDeleteView.as_view(), name='workload_delete'),
    
    # AJAX API
    path('ajax/create/', views.create_workload_ajax, name='create_workload_ajax'),
    path('ajax/update/', views.update_workload_ajax, name='update_workload_ajax'),
    path('ajax/delete/', views.delete_workload_ajax, name='delete_workload_ajax'),
]