from django.urls import path
from . import views

app_name = 'workloads'

urlpatterns = [
    path('', views.WorkloadCalendarView.as_view(), name='workload_list'),
    path('calendar/', views.WorkloadCalendarView.as_view(), name='workload_calendar'),
    # AJAX用URL
    path('ajax/save/', views.save_workload_ajax, name='save_workload_ajax'),
    path('ajax/create/', views.create_workload_ajax, name='create_workload_ajax'),
    
    # 既存のURL（互換性のため）
    path('detail/<int:pk>/', views.WorkloadDetailView.as_view(), name='workload_detail'),
    path('create/', views.WorkloadCreateView.as_view(), name='workload_create'),
    path('edit/<int:pk>/', views.WorkloadUpdateView.as_view(), name='workload_edit'),
    path('delete/<int:pk>/', views.WorkloadDeleteView.as_view(), name='workload_delete'),
]