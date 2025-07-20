from django.urls import path
from . import views

app_name = 'workloads'

urlpatterns = [
    # 工数カレンダー
    path('', views.WorkloadCalendarView.as_view(), name='workload_calendar'),
    
    # AJAX API
    path('ajax/create/', views.create_workload_ajax, name='create_workload_ajax'),
    path('ajax/update/', views.update_workload_ajax, name='update_workload_ajax'),
    path('ajax/delete/', views.delete_workload_ajax, name='delete_workload_ajax'),

]