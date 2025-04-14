from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user_or_ip', rate='10/m')
def product_catalog(request):
    # Get all products
    products = Product.objects.all()
    
    # Filter by brand if parameter exists
    brand_filter = request.GET.get('brand')
    if brand_filter:
        products = products.filter(brand=brand_filter)
    
    # Filter by gender if parameter exists
    gender_filter = request.GET.get('gender')
    if gender_filter:
        products = products.filter(gender=gender_filter)
    
    # Filter by size if parameter exists
    size_filter = request.GET.get('size')
    if size_filter:
        # Filter products where the size field contains the selected size
        filtered_products = []
        for product in products:
            sizes = product.get_sizes()
            if sizes and int(size_filter) in sizes:
                filtered_products.append(product.product_id)
        
        products = products.filter(product_id__in=filtered_products)
    
    # Get list of brands for filter - fix duplicates by converting to set and then sorted list
    brands_raw = Product.objects.values_list('brand', flat=True)
    brands = sorted(set(brands_raw))
    
    # Get all possible sizes for filter
    all_sizes = set()
    for product in Product.objects.all():
        sizes = product.get_sizes()
        if sizes:
            all_sizes.update(sizes)
    
    # Convert to sorted list
    sizes = sorted(list(all_sizes))
    
    context = {
        'products': products,
        'brands': brands,
        'sizes': sizes,
        'selected_brand': brand_filter,
        'selected_gender': gender_filter,
        'selected_size': size_filter,
    }
    
    if request.user.is_authenticated:
        context['is_admin'] = request.user.is_staff
    
    return render(request, 'catalog.html', context)

@login_required
@ratelimit(key='user_or_ip', rate='10/m')
def product_detail(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
        context = {
            'product': product,
            'images': product.get_images(),
            'is_admin': request.user.is_staff
        }
        return render(request, 'product_detail.html', context)
    except Product.DoesNotExist:
        messages.error(request, "Produk tidak ditemukan")
        return redirect('products:catalog')

@login_required
@ratelimit(key='user_or_ip', rate='10/m')
def get_product(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    
    # Get sizes with stock data
    sizes_with_stock = []
    for size_obj in product.sizes.all():
        sizes_with_stock.append({
            'size': size_obj.size,
            'stock': size_obj.stock
        })
    
    data = {
        'product_id': product.product_id,
        'name': product.name,
        'brand': product.brand,
        'gender': product.gender,
        'price': product.price,
        'sizes': sizes_with_stock,
        'image_url': product.image_url
    }
    return JsonResponse(data)

def get_product_data(request):
    products = Product.objects.all()
    product_list = []
    
    for product in products:
        product_list.append({
            'product_id': product.product_id,
            'brand': product.brand,
            'name': product.name,
            'price': product.price,
            'sizes': product.get_sizes(),
            'image_url': product.main_image()
        })
    
    return JsonResponse({'products': product_list})
