from django.db import models
from django.conf import settings
from transaction.models import Transaction

# Create your models here.

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('view', 'View'),
        ('add', 'Add'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('status_change', 'Status Change'),
        ('cancel', 'Cancel'),
        ('unauthorized', 'Unauthorized Access'),
        ('suspicious', 'Suspicious Activity'),
    ]
    
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='admin_audit_logs')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_audit_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.admin_user} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
