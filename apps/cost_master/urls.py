from django.urls import path
from . import views

app_name = 'cost_master'

urlpatterns = [
    # コストマスター関連
    path('', views.CostMasterListView.as_view(), name='cost_master_list'),
    path('create/', views.CostMasterCreateView.as_view(), name='cost_master_create'),
    path('<int:pk>/', views.CostMasterDetailView.as_view(), name='cost_master_detail'),
    path('<int:pk>/edit/', views.CostMasterUpdateView.as_view(), name='cost_master_edit'),
    
    # 取引先別請求単価関連
    path('client-rates/', views.ClientBillingRateListView.as_view(), name='client_billing_rate_list'),
    path('client-rates/create/', views.ClientBillingRateCreateView.as_view(), name='client_billing_rate_create'),
    path('client-rates/<int:pk>/', views.ClientBillingRateDetailView.as_view(), name='client_billing_rate_detail'),
    path('client-rates/<int:pk>/edit/', views.ClientBillingRateUpdateView.as_view(), name='client_billing_rate_edit'),
    path('client-rates/<int:pk>/delete/', views.ClientBillingRateDeleteView.as_view(), name='client_billing_rate_delete'),
    
    # 案件別コスト設定関連（追加）
    path('project-settings/', views.ProjectCostSettingListView.as_view(), name='project_cost_setting_list'),
    path('project-settings/create/', views.ProjectCostSettingCreateView.as_view(), name='project_cost_setting_create'),
    path('project-settings/<int:pk>/', views.ProjectCostSettingDetailView.as_view(), name='project_cost_setting_detail'),
    path('project-settings/<int:pk>/edit/', views.ProjectCostSettingUpdateView.as_view(), name='project_cost_setting_edit'),
    path('project-settings/<int:pk>/delete/', views.ProjectCostSettingDeleteView.as_view(), name='project_cost_setting_delete'),
    
    # AJAX API
    path('api/cost-master-data/', views.get_cost_master_data, name='get_cost_master_data'),
    path('api/cost-analysis/', views.cost_analysis_data, name='cost_analysis_data'),
]