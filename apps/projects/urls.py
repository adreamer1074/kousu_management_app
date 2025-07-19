from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # プロジェクト管理
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    
    # プロジェクトメンバー管理
    path('<int:project_pk>/members/', views.ProjectMemberListView.as_view(), name='project_member_list'),
    path('<int:project_pk>/members/add/', views.ProjectMemberCreateView.as_view(), name='project_member_add'),
    path('<int:project_pk>/members/<int:pk>/edit/', views.ProjectMemberUpdateView.as_view(), name='project_member_edit'),
    path('<int:project_pk>/members/<int:pk>/delete/', views.ProjectMemberDeleteView.as_view(), name='project_member_delete'),
    
    # プロジェクトフェーズ管理
    path('<int:project_pk>/phases/', views.ProjectPhaseListView.as_view(), name='project_phase_list'),
    path('<int:project_pk>/phases/add/', views.ProjectPhaseCreateView.as_view(), name='project_phase_add'),
    path('<int:project_pk>/phases/<int:pk>/edit/', views.ProjectPhaseUpdateView.as_view(), name='project_phase_edit'),
    path('<int:project_pk>/phases/<int:pk>/delete/', views.ProjectPhaseDeleteView.as_view(), name='project_phase_delete'),
    
    # AJAX
    path('ajax/load-projects/', views.load_projects, name='ajax_load_projects'),
]