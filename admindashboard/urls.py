from django.urls import path
from .views import (
    admin_page, add_product, 
    edit_product, delete_product,
    # Add transaction management views
    admin_transaction_list, admin_transaction_detail,
    admin_update_transaction_status, admin_cancel_transaction,
    admin_audit_logs, admin_product_audit_logs
)

app_name = 'admindashboard'

urlpatterns = [
    path('', admin_page, name='admin_page'),
    path('add-product/', add_product, name='add_product'),
    path('edit-product/<str:product_id>/', edit_product, name='edit_product'),
    path('delete-product/<str:product_id>/', delete_product, name='delete_product'),
    path('product-audit-logs/', admin_product_audit_logs, name='product_audit_logs'),
    
    # Transaction management URLs
    path('transactions/', admin_transaction_list, name='admin_transaction_list'),
    path('transactions/<str:transaction_id>/', admin_transaction_detail, name='admin_transaction_detail'),
    path('transactions/<str:transaction_id>/update-status/', admin_update_transaction_status, name='admin_update_status'),
    path('transactions/<str:transaction_id>/cancel/', admin_cancel_transaction, name='admin_cancel_transaction'),
    path('audit-logs/', admin_audit_logs, name='admin_audit_logs'),
] 