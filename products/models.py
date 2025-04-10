from django.db import models
import json

class Product(models.Model):
    BRAND_CHOICES = [
        ('Nike', 'Nike'),
        ('Adidas', 'Adidas'),
    ]
    
    brand = models.CharField(max_length=50, choices=BRAND_CHOICES)
    name = models.CharField(max_length=255)
    product_id = models.CharField(max_length=50, unique=True)
    price = models.IntegerField()
    size = models.TextField(help_text="Store sizes as JSON array, e.g. [36, 37, 38, 40, 42]")
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
    
    def get_sizes(self):
        """
        Returns list of available sizes
        """
        try:
            # Try to parse as JSON list
            return json.loads(self.size)
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, return as single size number
            return [int(self.size)] if self.size else []
    
    def main_image(self):
        """Returns the first image from the list or the single image"""
        images = self.get_images()
        if isinstance(images, list) and images:
            return images[0]
        return self.image_url
    
    def __str__(self):
        sizes = self.get_sizes()
        size_range = f"Sizes {min(sizes)}-{max(sizes)}" if sizes else "No sizes"
        return f"{self.brand} - {self.name} ({size_range})"
    
    class Meta:
        ordering = ['brand', 'name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
