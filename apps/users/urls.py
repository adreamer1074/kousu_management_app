from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # 認証関連
    path('register/', views.register, name='register'),
    
    # ユーザー管理
    path('list/', views.UserListView.as_view(), name='user_list'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    # path('<int:pk>/debug/', views.user_detail_debug, name='user_detail_debug'),  # デバッグ用
    path('<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'), 
    path('users/<int:pk>/permanent-delete/', views.UserPermanentDeleteView.as_view(), name='user_permanent_delete'), 

    
    # 部署管理
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    
    # 課管理
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/<int:pk>/', views.SectionDetailView.as_view(), name='section_detail'),
    path('sections/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<int:pk>/edit/', views.SectionUpdateView.as_view(), name='section_edit'),
    path('sections/<int:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
    
    # AJAX
    path('ajax/user/delete/', views.user_delete_ajax, name='user_delete_ajax'),
    path('ajax/user/restore/', views.user_restore_ajax, name='user_restore_ajax'),
        path('ajax/user/permanent-delete/', views.user_permanent_delete_ajax, name='user_permanent_delete_ajax'), 
    path('ajax/user/cleanup/', views.cleanup_inactive_users, name='cleanup_inactive_users'), 
    path('ajax/load-sections/', views.load_sections, name='ajax_load_sections'),
]