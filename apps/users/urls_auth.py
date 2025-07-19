from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'auth'

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.register, name='register'),
]