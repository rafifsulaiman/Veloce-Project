from django import forms
from .models import Transaction

class CheckoutForm(forms.Form):
    address = forms.CharField(
        label="Shipping Address",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your shipping address'})
    )
    city = forms.CharField(
        label="City",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your city'})
    )
    postal_code = forms.CharField(
        label="Postal Code",
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your postal code'})
    )
    payment_method = forms.ChoiceField(
        label="Payment Method",
        choices=Transaction.PAYMENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    delivery_price = forms.DecimalField(
        label="Delivery Price",
        initial=0,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Delivery price'})
    ) 