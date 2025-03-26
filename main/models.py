from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import re
import json

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

def validate_email(value):
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, value):
        raise ValidationError('Format email tidak valid. Contoh: user@example.com')
    
class CustomUser(AbstractUser):
    email = models.CharField(
            max_length=255, 
            unique=True, 
            validators=[validate_email]  # Validasi email manual
        )
    image_url = models.CharField(max_length=255, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    location = models.CharField(max_length=50, blank=True, null=True, default="Indonesia")
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    @property
    def is_regular_user(self):
        return not self.is_admin and not self.is_superuser

class Product(models.Model):
    BRAND_CHOICES = [
        ('Nike', 'Nike'),
        ('Adidas', 'Adidas'),
    ]
    
    brand = models.CharField(max_length=50, choices=BRAND_CHOICES)
    name = models.CharField(max_length=255)
    product_id = models.CharField(max_length=50, unique=True)
    price = models.IntegerField()
    size = models.IntegerField()
    image_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_images(self):
        """
        Returns list of image URLs if stored as JSON string,
        otherwise returns single image URL
        """
        try:
            # Try to parse as JSON list
            return json.loads(self.image_url)
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, return as single URL
            return [self.image_url]
    
    def main_image(self):
        """Returns the first image from the list or the single image"""
        images = self.get_images()
        if isinstance(images, list) and images:
            return images[0]
        return self.image_url
    
    def __str__(self):
        return f"{self.brand} - {self.name} (Size {self.size})"
    
    class Meta:
        ordering = ['brand', 'name', 'size']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'