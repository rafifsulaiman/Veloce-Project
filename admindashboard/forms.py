import json, re
from django import forms
from django.core.exceptions import ValidationError
from products.models import Product, ProductSize
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests

# only allow letters, numbers, spaces, hyphens and underscores
SAFE_TEXT_REGEX = re.compile(r'^[\w\s\-]+$')

def validate_safe_text(value):
    if not SAFE_TEXT_REGEX.match(value):
        raise ValidationError(
            "Invalid characters detected. Only letters, numbers, spaces, hyphens and underscores are allowed."
        )

class ProductForm(forms.ModelForm):
    # Define a size field to handle multiple sizes
    AVAILABLE_SIZES = [(str(size), str(size)) for size in range(16, 61)]
    
    sizes = forms.MultipleChoiceField(
        choices=AVAILABLE_SIZES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'inline-checkbox'}),
        required=True,
        help_text="Select all available sizes"
    )
    
    class Meta:
        model = Product
        fields = ['brand', 'name', 'product_id', 'price', 'image_url']
        widgets = {
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_id': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image_url': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        # attach our regex validator to the two free‐text fields
        validators = {
            'name': [validate_safe_text],
            'product_id': [validate_safe_text],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we're editing an existing product, populate the sizes field
        if self.instance.pk:
            try:
                current_sizes = self.instance.get_sizes()
                self.fields['sizes'].initial = [str(size) for size in current_sizes]
            except:
                self.fields['sizes'].initial = []

    def clean_image_url(self):
        url_field = self.cleaned_data.get('image_url', '')
        # very naive check: disallow common SQL chars
        if "'" in url_field or '"' in url_field or ";" in url_field:
            raise ValidationError("Invalid characters in image URL.")
        return url_field

    def save(self, commit=True):
        product = super().save(commit=False)
        
        if commit:
            product.save()
            
            # Get the sizes data from the form
            sizes = [int(size) for size in self.cleaned_data.get('sizes', [])]
            
            # Clear existing ProductSize objects if we're editing
            if product.pk:
                product.sizes.all().delete()
            
            # Create new ProductSize objects for each selected size
            for size in sizes:
                ProductSize.objects.create(
                    product=product,
                    size=size,
                    stock=0  # Default stock is 0
                )
                
        return product
