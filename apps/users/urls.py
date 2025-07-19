from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # ユーザー管理
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('list/', views.UserListView.as_view(), name='user_list'),
    path('<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('<int:pk>/detail/', views.UserDetailView.as_view(), name='user_detail'),
    
    # 部署管理
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    
    # 課管理
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<int:pk>/', views.SectionDetailView.as_view(), name='section_detail'),
    path('sections/<int:pk>/edit/', views.SectionUpdateView.as_view(), name='section_edit'),
    path('sections/<int:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
    
    # AJAX
    path('ajax/load-sections/', views.load_sections, name='ajax_load_sections'),
]