from django.urls import path
from .views import register, show_main, user_login, user_logout, product_catalog, product_detail, admin_page, add_product, edit_product, delete_product
from django.contrib.staticfiles.storage import staticfiles_storage # for `favicon` -> https://simpleit.rocks/python/django/django-favicon-adding/


app_name = 'main'

urlpatterns = [
    path('show_main/', show_main, name='show_main'),
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('catalog/', product_catalog, name='product_catalog'),
    path('product/<str:product_id>/', product_detail, name='product_detail'),
    path('', user_login, name='index'),
    path('admin-page/', admin_page, name='admin_page'),
    path('add-product/', add_product, name='add_product'),
    path('edit-product/<str:product_id>/', edit_product, name='edit_product'),
    path('delete-product/<str:product_id>/', delete_product, name='delete_product'),
]
