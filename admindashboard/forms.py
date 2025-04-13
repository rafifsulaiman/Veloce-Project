from django import forms
from products.models import Product

class ProductForm(forms.ModelForm):
    # Define a size field to handle multiple sizes
    AVAILABLE_SIZES = [(str(size), str(size)) for size in range(36, 46)]
    
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we're editing an existing product, populate the sizes field
        if self.instance.pk:
            try:
                current_sizes = self.instance.get_sizes()
                self.fields['sizes'].initial = [str(size) for size in current_sizes]
            except:
                self.fields['sizes'].initial = []
    
    def save(self, commit=True):
        product = super().save(commit=False)
        # Convert selected sizes to JSON
        import json
        sizes = [int(size) for size in self.cleaned_data.get('sizes', [])]
        product.size = json.dumps(sizes)
        
        if commit:
            product.save()
        return product 