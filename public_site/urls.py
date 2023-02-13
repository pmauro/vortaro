from django.urls import path

from . import views

urlpatterns = [
    path('', views.list, name='list'),
    path('words/<str:word>/', views.definition, name='definition'),
]