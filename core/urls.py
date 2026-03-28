from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('translate/', views.translate, name='translate'),
    path('download/<str:token>/', views.download, name='download'),
]
