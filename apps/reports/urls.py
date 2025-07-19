from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_report, name='generate_report'),
    path('view/<int:report_id>/', views.view_report, name='view_report'),
    path('download/<int:report_id>/', views.download_report, name='download_report'),
]