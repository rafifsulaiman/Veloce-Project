from django.db import models
from django.conf import settings
from products.models import Product

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.IntegerField()  # Store the selected size
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s cart - {self.product.name} (Size {self.size})"
    
    @property
    def subtotal(self):
        return self.product.price * self.quantity
