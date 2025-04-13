from django.urls import path
from .views import (
    product_catalog, product_detail, admin_page, add_product, 
    edit_product, delete_product, get_product, get_product_data
)

app_name = 'products'

urlpatterns = [
    path('catalog/', product_catalog, name='catalog'),
    path('product/<str:product_id>/', product_detail, name='product_detail'),
    path('admin-page/', admin_page, name='admin_page'),
    path('add-product/', add_product, name='add_product'),
    path('admin-page/edit-product/<str:product_id>/', edit_product, name='edit_product'),
    path('admin-page/delete-product/<str:product_id>/', delete_product, name='delete_product'),
    path('admin-page/get-product/<str:product_id>/', get_product, name='get_product'),
    path('get-product-data/', get_product_data, name='get_product_data'),
] 