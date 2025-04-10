from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'brand', 'name', 'price', 'get_size_range')
    search_fields = ('product_id', 'brand', 'name')
    list_filter = ('brand',)
    
    def get_size_range(self, obj):
        sizes = obj.get_sizes()
        if sizes:
            return f"{min(sizes)} - {max(sizes)}"
        return "No sizes"
    
    get_size_range.short_description = 'Size Range'
