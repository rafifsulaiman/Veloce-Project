from django.urls import path
from .views import register, show_main

urlpatterns = [
    path('show_main/', show_main, name='show_main'),
    path('', register, name='register'),
]
