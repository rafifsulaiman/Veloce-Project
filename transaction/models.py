from django.db import models
from django.conf import settings
from cart.models import CartItem
from products.models import Product

class Transaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    SHIPPING_STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('e_wallet', 'E-Wallet'),
    ]
    
    # Fields based on ER Diagram
    transaction_id = models.CharField(max_length=100, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Additional fields for shipping and user information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shipping_status = models.CharField(max_length=20, choices=SHIPPING_STATUS_CHOICES, default='processing')
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.user.username}"
    
    @property
    def product_price(self):
        """Calculate the total price of products without delivery fee"""
        return self.transaction_amount - self.delivery_price
    
    @property
    def current_status(self):
        if self.status == 'failed':
            return 'Failed'
        elif self.status == 'pending':
            return 'Pending Payment'
        elif self.shipping_status == 'processing':
            return 'Processing'
        elif self.shipping_status == 'shipped':
            return 'Shipped'
        elif self.shipping_status == 'delivered':
            return 'Delivered'
        elif self.shipping_status == 'cancelled':
            return 'Cancelled'
        return 'Unknown'

class OrderItem(models.Model):
    transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)  # Store name at time of purchase
    product_price = models.DecimalField(max_digits=10, decimal_places=2)  # Store price at time of purchase
    quantity = models.PositiveIntegerField()
    size = models.IntegerField()
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Size {self.size})"
    
    @property
    def subtotal(self):
        return self.product_price * self.quantity
