from django.shortcuts import render, redirect, get_object_or_404
from admindashboard.forms import ProductForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from products.models import Product
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

@login_required(login_url='users:login')
def admin_page(request):
    if not request.user.is_staff:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('products:catalog')
    
    product = Product.objects.all()
    
    context = {
        'products': product
    }
    
    return render(request, 'admin_page.html', context)
    
@login_required(login_url='users:login')
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
    return render(request, 'add_product.html', {'form': form})

@login_required(login_url='users:login')
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
            
            sizes = data.get('sizes')
            if sizes:
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

@login_required(login_url='users:login')
def delete_product(request, product_id):
    if not request.user.is_staff:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('products:catalog')
    
    product = get_object_or_404(Product, product_id=product_id)
    product.delete()
    messages.success(request, f"Produk {product.name} berhasil dihapus.")
    return redirect('admindashboard:admin_page')