from django.urls import path
from .views import (
    admin_page, add_product, 
    edit_product, delete_product, get_product, get_product_data
)

app_name = 'admin'

urlpatterns = [
    path('admin-page/', admin_page, name='admin_page'),
    path('add-product/', add_product, name='add_product'),
    path('edit-product/<str:product_id>/', edit_product, name='edit_product'),
    path('delete-product/<str:product_id>/', delete_product, name='delete_product'),
    path('get-product/<str:product_id>/', get_product, name='get_product'),
    path('get-product-data/', get_product_data, name='get_product_data'),
] 