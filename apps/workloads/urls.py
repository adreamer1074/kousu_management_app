from django.urls import path
from . import views

app_name = 'workloads'

urlpatterns = [
    # 通常のビュー
    path('', views.WorkloadCalendarView.as_view(), name='workload_calendar'),
    path('create/', views.WorkloadCreateView.as_view(), name='workload_create'),
    path('<int:pk>/edit/', views.WorkloadUpdateView.as_view(), name='workload_edit'),
    path('<int:pk>/delete/', views.WorkloadDeleteView.as_view(), name='workload_delete'),
    
    # AJAX用のURL（新規追加）
    path('ajax/create/', views.create_workload_ajax, name='create_workload_ajax'),
    path('ajax/update/', views.update_workload_ajax, name='update_workload_ajax'),
    path('ajax/bulk-update/', views.bulk_update_workload_ajax, name='bulk_update_workload_ajax'),
    path('ajax/delete/', views.delete_workload_ajax, name='delete_workload_ajax'),
]