from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 認証関連（ルートレベル）
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), 
    path('register/', user_views.register, name='register'),
    
    # メインページ
    path('', include('apps.core.urls')),
    
    # ユーザー管理
    path('users/', include('apps.users.urls')),
]