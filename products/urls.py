from django.urls import path
from .views import (
    product_catalog, product_detail,  get_product, get_product_data
)

app_name = 'products'

urlpatterns = [
    path('catalog/', product_catalog, name='catalog'),
    path('product/<str:product_id>/', product_detail, name='product_detail'),
    path('get-product-data/', get_product_data, name='get_product_data'),
    path('get-product/<str:product_id>/', get_product, name='get_product'),
] 