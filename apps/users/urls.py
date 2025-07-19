from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # ユーザー管理
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('list/', views.UserListView.as_view(), name='user_list'),
    path('<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('<int:pk>/detail/', views.UserDetailView.as_view(), name='user_detail'),
]