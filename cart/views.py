from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CartItem
from products.models import Product

@login_required
def cart_view(request):
    """
    View for displaying the user's shopping cart
    Admin users are restricted from accessing this page
    """
    if request.user.is_staff:
        messages.error(request, "Admin users cannot access the shopping cart.")
        return redirect('products:catalog')
    
    # Get all cart items for the current user
    cart_items = CartItem.objects.filter(user=request.user)
    
    context = {
        "user": request.user,
        "cart_items": cart_items,
        "total": sum(item.subtotal for item in cart_items)
    }
    return render(request, 'cart/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    """Add a product to the user's cart"""
    if request.user.is_staff:
        messages.error(request, "Admin users cannot add items to cart.")
        return redirect('products:catalog')
    
    if request.method == 'POST':
        try:
            product = Product.objects.get(product_id=product_id)
            size = int(request.POST.get('size'))
            quantity = int(request.POST.get('quantity', 1))
            
            # Check if product with this size already exists in cart
            existing_item = CartItem.objects.filter(
                user=request.user,
                product=product,
                size=size
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
                existing_item.save()
                messages.success(request, f"Updated quantity of {product.name} (Size {size}) in your cart.")
            else:
                CartItem.objects.create(
                    user=request.user,
                    product=product,
                    size=size,
                    quantity=quantity
                )
                messages.success(request, f"Added {product.name} (Size {size}) to your cart.")
                
            return redirect('products:product_detail', product_id=product_id)
            
        except Product.DoesNotExist:
            messages.error(request, "Product not found.")
            return redirect('products:catalog')
        except ValueError:
            messages.error(request, "Please select a valid size and quantity.")
            return redirect('products:product_detail', product_id=product_id)
    
    return redirect('products:product_detail', product_id=product_id)

@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    if request.user.is_staff:
        messages.error(request, "Admin users cannot access the shopping cart.")
        return redirect('products:catalog')
    
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        cart_item.delete()
        messages.success(request, f"Removed {cart_item.product.name} from your cart.")
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in your cart.")
    
    return redirect('cart:cart')
