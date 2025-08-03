from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # プロジェクト関連のURL
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),

    # チケット管理（統一されたパターン）
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'), 
    path('tickets/create/', views.ProjectTicketCreateView.as_view(), name='ticket_create_global'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:pk>/edit/', views.TicketUpdateView.as_view(), name='ticket_edit'),
    path('tickets/<int:pk>/delete/', views.TicketDeleteView.as_view(), name='ticket_delete'),
    
    # プロジェクト別チケット管理
    path('<int:project_pk>/tickets/', views.TicketListView.as_view(), name='ticket_list'),  # 引数ありの同じ名前
    path('<int:project_pk>/tickets/create/', views.ProjectTicketCreateView.as_view(), name='ticket_create'),
    
    # API関連のURL
    path('api/<int:project_id>/tickets/', views.get_project_tickets_api, name='get_project_tickets_api'),
    path('api/tickets/', views.get_tickets_api, name='get_tickets_api'),
]