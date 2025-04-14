from django.contrib import admin
from .models import Transaction, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'product_price', 'quantity', 'size', 'subtotal']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'transaction_amount', 'status', 'shipping_status', 'date_created']
    list_filter = ['status', 'shipping_status', 'date_created']
    search_fields = ['transaction_id', 'user__username', 'shipping_address']
    date_hierarchy = 'date_created'
    readonly_fields = ['transaction_id', 'user', 'transaction_amount', 'date_created', 'updated_at']
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'product_name', 'size', 'quantity', 'product_price', 'subtotal']
    list_filter = ['transaction__status', 'transaction__shipping_status', 'transaction__date_created']
    search_fields = ['transaction__transaction_id', 'product_name']
    readonly_fields = ['subtotal']
