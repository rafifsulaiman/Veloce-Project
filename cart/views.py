from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CartItem
from products.models import Product, ProductSize

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
            
            # Validate size and stock availability
            product_size = ProductSize.objects.filter(product=product, size=size).first()
            if not product_size:
                messages.error(request, f"Size {size} is not available for this product.")
                return redirect('products:product_detail', product_id=product_id)
            
            if product_size.stock < quantity:
                messages.error(request, f"Requested quantity exceeds available stock. Only {product_size.stock} items available.")
                return redirect('products:product_detail', product_id=product_id)
            
            # Check if product with this size already exists in cart
            existing_item = CartItem.objects.filter(
                user=request.user,
                product=product,
                size=size
            ).first()
            
            if existing_item:
                # Check if combined quantity exceeds stock
                if existing_item.quantity + quantity > product_size.stock:
                    messages.error(request, f"Cannot add more items. Maximum available stock is {product_size.stock}.")
                    return redirect('products:product_detail', product_id=product_id)
                
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
                
            return redirect('cart:cart')
            
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
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f"Removed {product_name} from your cart.")
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in your cart.")
    
    return redirect('cart:cart')

@login_required
def update_quantity(request, item_id):
    """Update the quantity of an item in the cart"""
    if request.user.is_staff:
        messages.error(request, "Admin users cannot access the shopping cart.")
        return redirect('products:catalog')
    
    if request.method != 'POST':
        return redirect('cart:cart')
    
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        action = request.POST.get('action')
        
        # Get current stock from ProductSize
        product_size = ProductSize.objects.get(
            product=cart_item.product, 
            size=cart_item.size
        )
        
        if action == 'increase':
            # Check stock availability before increasing
            if cart_item.quantity < product_size.stock:
                cart_item.quantity += 1
                cart_item.save()
            else:
                messages.error(request, f"Cannot add more items. Maximum available stock is {product_size.stock}.")
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                # If trying to decrease below 1, remove the item
                cart_item.delete()
                messages.success(request, f"Removed {cart_item.product.name} from your cart.")
        
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in your cart.")
    except ProductSize.DoesNotExist:
        messages.error(request, "Product size not available.")
    
    return redirect('cart:cart')
