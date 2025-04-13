from django.db import models
import json

class Product(models.Model):
    BRAND_CHOICES = [
        ('Nike', 'Nike'),
        ('Adidas', 'Adidas'),
    ]
    
    GENDER_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('unisex', 'Unisex'),
    ]
    
    brand = models.CharField(max_length=50, choices=BRAND_CHOICES)
    name = models.CharField(max_length=255)
    product_id = models.CharField(max_length=50, unique=True)
    price = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
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
        return [size.size for size in self.sizes.all()]
    
    def get_sizes_with_stock(self):
        """
        Returns list of dictionaries with size and stock information
        """
        return list(self.sizes.values('size', 'stock'))
    
    def main_image(self):
        """Returns the first image from the list or the single image"""
        images = self.get_images()
        if isinstance(images, list) and images:
            return images[0]
        return self.image_url
    
    def __str__(self):
        sizes = self.get_sizes()
        size_range = f"Sizes {min(sizes)}-{max(sizes)}" if sizes else "No sizes"
        return f"{self.brand} - {self.name} ({size_range}) - {self.get_gender_display()}"
    
    class Meta:
        ordering = ['brand', 'name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
    
    @classmethod
    def from_csv_row(cls, row):
        """
        Create or update a product from a CSV row
        Returns tuple of (product, created_or_updated)
        """
        # Get or create the product
        product, created = cls.objects.get_or_create(
            product_id=row['product_id'],
            defaults={
                'brand': row['brand'],
                'name': row['name'],
                'price': int(row['price']),
                'gender': row['gender'],
                'image_url': row['image_url']
            }
        )
        
        # If product already exists, update it
        if not created:
            product.brand = row['brand']
            product.name = row['name']
            product.price = int(row['price'])
            product.gender = row['gender']
            product.image_url = row['image_url']
            product.save()
        
        # Create or update the size with stock
        size = int(row['size'])
        stock = int(row['stock'])
        
        size_obj, _ = ProductSize.objects.update_or_create(
            product=product,
            size=size,
            defaults={'stock': stock}
        )
        
        return product, created

class ProductSize(models.Model):
    product = models.ForeignKey(Product, related_name='sizes', on_delete=models.CASCADE)
    size = models.IntegerField()
    stock = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['product', 'size']
        ordering = ['size']
    
    def __str__(self):
        return f"{self.product.name} - Size {self.size} (Stock: {self.stock})"
