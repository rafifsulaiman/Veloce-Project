from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm, ProductForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Product
from django.http import JsonResponse
import json

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
    
def admin_page(request):
    if not request.user.is_admin:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('main:product_catalog')
    
    product = Product.objects.all()
    # print(product)
    
    context = {
        'products': product
    }
    
    return render(request, 'admin_page.html', context)
    
@login_required
def add_product(request):
    if not request.user.is_admin:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('main:product_catalog')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produk berhasil ditambahkan.")
            return redirect('main:product_catalog')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

@login_required
def edit_product(request, product_id):
    if not request.user.is_admin:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('main:product_catalog')
    print(f"Fetching product with product_id: {product_id}")
    product = get_object_or_404(Product, product_id=product_id)

    if request.method == 'GET':  # Tambahkan ini untuk menangani GET request
        return JsonResponse({  
            'name': product.name,
            'price': product.price,
            'size': product.size,
            'image_url': product.image_url,
        })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            product.name = data.get('name', product.name)
            product.price = data.get('price', product.price)
            product.size = data.get('size', product.size)
            product.image_url = data.get('image_url', product.image_url)

            product.save(update_fields=['name', 'price', 'size', 'image_url'])
            return JsonResponse({'message': "Produk berhasil diubah."})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': "Method Not Allowed"}, status=405)

def get_product_data(request):
    products = Product.objects.all()  # Ambil semua produk

    product_list = [
        {
            'product_id': product.product_id,
            'brand': product.brand,
            'name': product.name,
            'price': product.price,
            'size': product.size,
            'image_url': product.image_url,
        }
        for product in products
    ]

    return JsonResponse({'products': product_list})

@login_required
def delete_product(request, product_id):
    if not request.user.is_admin:
        return JsonResponse({'error': "Anda tidak memiliki izin untuk mengakses halaman ini."}, status=403)
    
    product = get_object_or_404(Product, product_id=product_id)
    product.delete()
    return JsonResponse({'message': "Produk berhasil dihapus."})