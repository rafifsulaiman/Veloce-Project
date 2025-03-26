from django.urls import path
from .views import register, show_main
from django.contrib.staticfiles.storage import staticfiles_storage # for `favicon` -> https://simpleit.rocks/python/django/django-favicon-adding/


urlpatterns = [
    path('show_main/', show_main, name='show_main'),
    path('', register, name='register'),
]
