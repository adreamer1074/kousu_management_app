from django.urls import path
from . import views

urlpatterns = [
    path('', views.WorkloadListView.as_view(), name='workload-list'),
    path('create/', views.WorkloadCreateView.as_view(), name='workload-create'),
    path('<int:pk>/', views.WorkloadDetailView.as_view(), name='workload-detail'),
    path('<int:pk>/update/', views.WorkloadUpdateView.as_view(), name='workload-update'),
    path('<int:pk>/delete/', views.WorkloadDeleteView.as_view(), name='workload-delete'),
]