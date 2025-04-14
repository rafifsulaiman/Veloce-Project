from django.contrib import admin
from .models import Transaction, OrderItem

# Basic registration of models
admin.site.register(Transaction)
admin.site.register(OrderItem)
