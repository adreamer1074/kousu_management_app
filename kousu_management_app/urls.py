from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('users/', include('apps.users.urls')),
    path('projects/', include('apps.projects.urls')),
    path('workloads/', include('apps.workloads.urls')),
    path('reports/', include('apps.reports.urls')),

    # 認証関連
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', user_views.custom_logout, name='logout'),  # カスタムログアウトビューを使用
    path('register/', user_views.register, name='register'),
]