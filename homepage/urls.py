from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='homepage-index'),
    path('katalog/', views.katalog, name='homepage-katalog'),
]
