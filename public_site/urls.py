from django.urls import path

from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('words/<str:word>/', views.definition, name='definition'),
    path('twilio/', views.twilio_webhook, name='twilio')
]
