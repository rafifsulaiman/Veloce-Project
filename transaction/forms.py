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
    # Hanya menggunakan VelocePay sebagai metode pembayaran
    payment_method = forms.CharField(
        widget=forms.HiddenInput(),
        initial='velocepay'
    ) 