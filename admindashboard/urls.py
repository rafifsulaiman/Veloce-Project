from django.urls import path
from .views import (
    admin_page, add_product, 
    edit_product, delete_product
)

app_name = 'admindashboard'

urlpatterns = [
    path('', admin_page, name='admin_page'),
    path('add-product/', add_product, name='add_product'),
    path('edit-product/<str:product_id>/', edit_product, name='edit_product'),
    path('delete-product/<str:product_id>/', delete_product, name='delete_product'),
] 