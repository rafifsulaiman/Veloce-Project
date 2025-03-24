from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Create your views here.
def show_main(request):
    context = {
        "user": request.user
    }
    return render(request, 'main.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            admin_code = form.cleaned_data.get('admin_code')
            if admin_code == "PKPLASIK37":  
                user.is_admin = True
                user.is_staff = True
                
            user.save()
            login(request, user)
            return redirect('main:show_main')  
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})