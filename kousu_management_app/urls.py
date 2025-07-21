from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('users/', include('apps.users.urls')),
    path('projects/', include('apps.projects.urls')),
    path('workloads/', include('apps.workloads.urls')),
    path('reports/', include('apps.reports.urls')),
    path('cost-master/', include('apps.cost_master.urls')),  # 追加

    # 認証関連
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', user_views.custom_logout, name='logout'),  # カスタムログアウトビューを使用
    path('register/', user_views.register, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)