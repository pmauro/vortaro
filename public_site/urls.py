from django.urls import path

from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('wordz/<str:word>/', views.definition, name='definition'),
]
