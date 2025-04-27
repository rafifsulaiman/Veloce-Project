from django.urls import path
from .views import (
    checkout_view,
    checkout_confirm,
    transaction_success,
    order_history,
    order_detail,
    process_payment,
    cancel_order,
)

app_name = 'transaction'

urlpatterns = [
    # Customer facing URLs
    path('checkout/', checkout_view, name='checkout'),
    path('checkout/confirm/', checkout_confirm, name='checkout_confirm'),
    path('success/<str:transaction_id>/', transaction_success, name='success'),
    path('orders/', order_history, name='order_history'),
    path('orders/<str:transaction_id>/', order_detail, name='order_detail'),
    path('payment/<str:transaction_id>/', process_payment, name='process_payment'),
    # Admin cancel order
    path('orders/<str:transaction_id>/cancel/', cancel_order, name='cancel_order'),
]
