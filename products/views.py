from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

def product_catalog(request):
    # Get all products
    products = Product.objects.all()
    
    # Filter by brand if parameter exists
    brand_filter = request.GET.get('brand')
    if brand_filter:
        products = products.filter(brand=brand_filter)
    
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
    
    # Get list of brands for filter
    brands = Product.objects.values_list('brand', flat=True).distinct()
    
    # Get all possible sizes for filter
    all_sizes = set()
    for product in Product.objects.all():
        sizes = product.get_sizes()
        if sizes:
            all_sizes.update(sizes)
    
    # Convert to sorted list
    sizes = sorted(list(all_sizes))
    
    # Prepare context with basic information
    context = {
        'products': products,
        'brands': brands,
        'sizes': sizes,
        'selected_brand': brand_filter,
        'selected_size': size_filter,
    }
    
    # Add information about whether user is an admin
    if request.user.is_authenticated:
        context['is_admin'] = request.user.is_staff
    
    return render(request, 'products/catalog.html', context)

@login_required
def product_detail(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
        context = {
            'product': product,
            'images': product.get_images(),
            'is_admin': request.user.is_staff
        }
        return render(request, 'products/product_detail.html', context)
    except Product.DoesNotExist:
        messages.error(request, "Produk tidak ditemukan")
        return redirect('products:catalog')
    
@login_required
def admin_page(request):
    if not request.user.is_staff:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('products:catalog')
    
    products = Product.objects.all()
    
    # Calculate statistics for dashboard
    total_stock = sum(size.stock for product in products for size in product.sizes.all())
    brands_count = products.values('brand').distinct().count()
    
    # Get unique sizes count
    sizes = set()
    for product in products:
        sizes.update(product.get_sizes())
    sizes_count = len(sizes)
    
    context = {
        'products': products,
        'total_stock': total_stock,
        'brands_count': brands_count,
        'sizes_count': sizes_count
    }
    
    return render(request, 'products/admin_page.html', context)
    
@login_required
def add_product(request):
    if not request.user.is_staff:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('products:catalog')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produk berhasil ditambahkan.")
            return redirect('products:catalog')
    else:
        form = ProductForm()
    return render(request, 'products/add_product.html', {'form': form})

@login_required
@csrf_exempt
def edit_product(request, product_id):
    if not request.user.is_staff:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('products:catalog')

    product = get_object_or_404(Product, product_id=product_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            product.name = data.get('name', product.name)
            product.price = data.get('price', product.price)
            
            # Handle size as JSON array
            sizes = data.get('sizes')
            if sizes:
                # Convert to JSON string if it's a list
                if isinstance(sizes, list):
                    product.size = json.dumps(sizes)
                else:
                    product.size = sizes
                    
            product.image_url = data.get('image_url', product.image_url)

            product.save()
            return JsonResponse({'message': "Produk berhasil diubah."})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': "Method Not Allowed"}, status=405)

@login_required
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

@login_required
def delete_product(request, product_id):
    if not request.user.is_staff:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('products:catalog')
    
    product = get_object_or_404(Product, product_id=product_id)
    product.delete()
    messages.success(request, f"Produk {product.name} berhasil dihapus.")
    return redirect('products:admin_page')
