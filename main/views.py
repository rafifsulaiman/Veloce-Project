from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Product

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

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Berhasil login sebagai {username}")
                if user.is_admin:
                    return redirect('main:show_main')  # Redirect admin ke halaman admin
                else:
                    return redirect('main:show_main')  # Redirect user biasa ke halaman utama
            else:
                messages.error(request, "Username atau password salah.")
        else:
            messages.error(request, "Username atau password salah.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, "Berhasil logout.")
    return redirect('main:login')

@login_required
def product_catalog(request):
    # Ambil semua produk
    products = Product.objects.all()
    
    # Filter berdasarkan brand jika ada parameter
    brand_filter = request.GET.get('brand')
    if brand_filter:
        products = products.filter(brand=brand_filter)
    
    # Filter berdasarkan ukuran jika ada parameter
    size_filter = request.GET.get('size')
    if size_filter:
        products = products.filter(size=size_filter)
    
    # Ambil daftar brand dan ukuran untuk filter
    brands = Product.objects.values_list('brand', flat=True).distinct()
    sizes = Product.objects.values_list('size', flat=True).distinct().order_by('size')
    
    context = {
        'products': products,
        'brands': brands,
        'sizes': sizes,
        'selected_brand': brand_filter,
        'selected_size': size_filter,
    }
    
    return render(request, 'catalog.html', context)

@login_required
def product_detail(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
        context = {
            'product': product,
            'images': product.get_images()
        }
        return render(request, 'product_detail.html', context)
    except Product.DoesNotExist:
        messages.error(request, "Produk tidak ditemukan")
        return redirect('main:product_catalog')