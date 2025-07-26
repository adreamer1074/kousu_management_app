from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import CustomLoginView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 認証関連（カスタムログインビューを使用）
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # アプリのURL
    path('users/', include('apps.users.urls')),
    path('projects/', include('apps.projects.urls')),
    path('workloads/', include('apps.workloads.urls')),
    path('reports/', include('apps.reports.urls')),
    path('cost-master/', include('apps.cost_master.urls')),
    
    # ホームページ（coreアプリを使用
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)