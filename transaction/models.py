from django.db import models
from django.conf import settings
from cart.models import CartItem
from products.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class Transaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Menunggu Pembayaran'),
        ('paid', 'Pembayaran Berhasil'),
        ('processing', 'Pesanan Diproses'),
        ('failed', 'Pembayaran Gagal'),
        ('cancelled', 'Dibatalkan'),
    ]
    
    SHIPPING_STATUS_CHOICES = [
        ('processing', 'Diproses'),
        ('shipped', 'Dikirim'),
        ('delivered', 'Diterima'),
        ('cancelled', 'Dibatalkan'),
    ]
    
    PAYMENT_CHOICES = [
        ('velocepay', 'VelocePay'),
    ]
    
    # Fields based on ER Diagram
    transaction_id = models.CharField(max_length=100, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=25000)  # Fixed at Rp 25.000
    
    # Additional fields for shipping and user information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shipping_status = models.CharField(max_length=20, choices=SHIPPING_STATUS_CHOICES, default='processing')
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='velocepay')
    payment_url = models.CharField(max_length=255, blank=True, null=True)  # URL untuk pembayaran VelocePay
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.user.username}"
    
    @property
    def product_price(self):
        """Calculate the total price of products without delivery fee"""
        return self.transaction_amount - self.delivery_price
    
    @property
    def current_status(self):
        """Get current status for display"""
        return self.get_status_display()
    
    def process_payment(self):
        """Mark transaction as paid and update status"""
        if self.status == 'pending':
            self.status = 'processing'
            self.save()
            return True
        return False

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

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('view', 'View Transaction'),
        ('status_change', 'Status Change'),
        ('cancel', 'Cancel Transaction'),
        ('unauthorized', 'Unauthorized Access Attempt'),
        ('suspicious', 'Suspicious Activity'),
    ]
    
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.admin_user.username} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

# Signal to assign transaction permissions to staff users
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def assign_transaction_permissions(sender, instance, created, **kwargs):
    """
    Assigns transaction-related permissions to staff users
    This ensures that staff users can manage transactions properly
    """
    if instance.is_staff:
        # Get content type for the Transaction model
        transaction_content_type = ContentType.objects.get_for_model(Transaction)
        
        # Get the permissions for Transaction model
        change_permission = Permission.objects.get(
            codename='change_transaction',
            content_type=transaction_content_type,
        )
        
        delete_permission = Permission.objects.get(
            codename='delete_transaction',
            content_type=transaction_content_type,
        )
        
        # Get content type for the AuditLog model
        auditlog_content_type = ContentType.objects.get_for_model(AuditLog)
        
        # Get the permissions for AuditLog model
        view_audit_permission = Permission.objects.get(
            codename='view_auditlog',
            content_type=auditlog_content_type,
        )
        
        # Assign permissions to the user
        instance.user_permissions.add(change_permission)
        instance.user_permissions.add(delete_permission)
        instance.user_permissions.add(view_audit_permission)
