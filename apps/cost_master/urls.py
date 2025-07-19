from django.urls import path
from . import views

urlpatterns = [
    path('', views.cost_master_index, name='cost_master_index'),
    path('create/', views.create_cost, name='create_cost'),
    path('edit/<int:id>/', views.edit_cost, name='edit_cost'),
    path('delete/<int:id>/', views.delete_cost, name='delete_cost'),
]