from django import forms
from .models import Transaction
from users.models import Address

class CheckoutForm(forms.Form):
    address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        label="Shipping Address",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    # City and postal_code will be auto-filled from address
    payment_method = forms.CharField(
        widget=forms.HiddenInput(),
        initial='velocepay'
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['address'].queryset = Address.objects.filter(user=user) 