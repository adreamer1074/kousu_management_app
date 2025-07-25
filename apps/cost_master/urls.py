from django.urls import path
from . import views

app_name = 'cost_master'

urlpatterns = [
    # ダッシュボード
    path('', views.outsourcing_dashboard, name='dashboard'),
    
    # ビジネスパートナー管理
    path('business-partners/', views.BusinessPartnerListView.as_view(), name='business_partner_list'),
    path('business-partners/create/', views.BusinessPartnerCreateView.as_view(), name='business_partner_create'),
    path('business-partners/<int:pk>/edit/', views.BusinessPartnerUpdateView.as_view(), name='business_partner_update'),
    path('business-partners/<int:pk>/delete/', views.business_partner_delete, name='business_partner_delete'),
    
    # 外注費管理
    path('outsourcing-costs/', views.outsourcing_cost_list, name='outsourcing_cost_list'),
    path('outsourcing-costs/create/', views.outsourcing_cost_create, name='outsourcing_cost_create'),
    path('outsourcing-costs/<int:pk>/edit/', views.outsourcing_cost_update, name='outsourcing_cost_update'),
    path('outsourcing-costs/<int:pk>/delete/', views.outsourcing_cost_delete, name='outsourcing_cost_delete'),
    
    # API エンドポイント
    path('api/tickets/', views.get_project_tickets_api, name='get_project_tickets_api'),
    path('api/bp-rate/', views.get_bp_hourly_rate_api, name='get_bp_hourly_rate_api'),
    path('api/bp-projects/', views.get_bp_projects_api, name='get_bp_projects_api'),
]