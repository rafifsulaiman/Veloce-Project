from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import CustomUser
from django.core.exceptions import ValidationError
import re

def validate_email(value):
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, value):
        raise ValidationError('Format email tidak valid. Contoh: user@example.com')
    
class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'type': 'text'})
        self.fields['last_name'].widget.attrs.update({'type': 'text'})
        self.fields['email'].widget.attrs.update({'type': 'email'})
        self.fields['password1'].widget.attrs.update({'type': 'password'})
        self.fields['password2'].widget.attrs.update({'type': 'password'})
        
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'John'})
)
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Doe'})
)
    email = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'example@example.com'}),
        validators=[validate_email]  # Validasi email manual
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    admin_code = forms.CharField(required=False, help_text="Enter admin code if registering as admin")

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'admin_code')
        
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'username_example'}),
            # 'password1': forms.PasswordInput(attrs={'placeholder': 'password example'}),
            # 'password2': forms.PasswordInput(attrs={'placeholder': 'password example'}),
        }
        
    def save(self, commit=True):
        user = super().save(commit=False)  # Create user object without saving to database
        user.first_name = self.cleaned_data['first_name']  # Set first name
        user.last_name = self.cleaned_data['last_name']    # Set last name
        user.email = self.cleaned_data['email']            # Set email
        if commit:
            user.save()  # Save user to the database
        return user

    def clean_admin_code(self):
        admin_code = self.cleaned_data.get('admin_code')
        if admin_code and admin_code != "PKPLASIK37": 
            raise forms.ValidationError("Invalid admin code")
        return admin_code 

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    gender = forms.ChoiceField(choices=CustomUser.GENDER_CHOICES, required=False)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'gender', 'password1', 'password2']

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'gender', 'profile_pic_url']
        widgets = {
            'profile_pic_url': forms.URLInput(attrs={'placeholder': 'https://example.com/profile.jpg'}),
        } 