from django.urls import path

from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('menu/', views.menu, name='menu'),
    path('words/<str:word>/', views.definition, name='definition'),
]