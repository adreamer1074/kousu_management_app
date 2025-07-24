from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # プロジェクト関連のURL
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    
    # チケット関連のURL
    path('<int:project_pk>/tickets/create/', views.ProjectTicketCreateView.as_view(), name='ticket_create'),
    
    # API関連のURL
    path('api/tickets/', views.get_tickets_api, name='get_tickets_api'),
    path('api/<int:project_id>/tickets/', views.get_project_tickets_api, name='get_project_tickets_api'),  # 新規追加
]