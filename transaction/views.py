from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from django.db import transaction
from django.db.models import F, Sum
from django.urls import reverse
import uuid
import datetime
from decimal import Decimal

from cart.models import CartItem
from products.models import Product, ProductSize
from .models import Transaction, OrderItem
from .forms import CheckoutForm

# Nilai ongkir fixed
FIXED_DELIVERY_PRICE = 25000

@login_required(login_url='users:login')
def checkout_view(request):
    """Displays the checkout page with cart items and shipping form"""
    # Redirect admin users
    if request.user.is_staff:
        messages.error(request, "Admin users cannot checkout.")
        return redirect('products:catalog')
    
    # Get cart items
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Redirect if cart is empty
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart')
    
    # Initialize checkout form
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Store form data in session for confirmation step
            request.session['checkout_data'] = {
                'address': form.cleaned_data['address'],
                'city': form.cleaned_data['city'],
                'postal_code': form.cleaned_data['postal_code'],
                'payment_method': form.cleaned_data['payment_method'],
            }
            return redirect('transaction:checkout_confirm')
    else:
        form = CheckoutForm()
    
    # Calculate total
    cart_total = sum(item.subtotal for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'form': form,
        'delivery_price': FIXED_DELIVERY_PRICE,
        'total_with_delivery': cart_total + FIXED_DELIVERY_PRICE
    }
    
    return render(request, 'checkout.html', context)

@login_required(login_url='users:login')
def checkout_confirm(request):
    """Confirmation page before finalizing order"""
    # Redirect admin users
    if request.user.is_staff:
        messages.error(request, "Admin users cannot checkout.")
        return redirect('products:catalog')
    
    # Check if checkout data exists in session
    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.error(request, "Please complete the checkout form.")
        return redirect('transaction:checkout')
    
    # Get cart items
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Redirect if cart is empty
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart')
    
    # Calculate total for products
    product_total = sum(item.subtotal for item in cart_items)
    # Use fixed delivery price
    delivery_price = FIXED_DELIVERY_PRICE
    # Calculate final transaction amount
    transaction_amount = product_total + delivery_price
    
    if request.method == 'POST':
        # Process the order
        try:
            with transaction.atomic():
                # Check stock availability one last time
                for cart_item in cart_items:
                    product_size = ProductSize.objects.select_for_update().get(
                        product=cart_item.product,
                        size=cart_item.size
                    )
                    
                    if product_size.stock < cart_item.quantity:
                        messages.error(
                            request, 
                            f"Sorry, only {product_size.stock} units of {cart_item.product.name} in size {cart_item.size} are available."
                        )
                        return redirect('cart:cart')
                
                # Create transaction with fields based on ER diagram
                transaction_id = f"TRX-{uuid.uuid4().hex[:8].upper()}-{int(timezone.now().timestamp())}"
                new_transaction = Transaction.objects.create(
                    transaction_id=transaction_id,
                    user=request.user,
                    status='pending',  # Menunggu pembayaran
                    transaction_amount=transaction_amount,
                    delivery_price=delivery_price,
                    shipping_address=checkout_data['address'],
                    shipping_city=checkout_data['city'],
                    shipping_postal_code=checkout_data['postal_code'],
                    payment_method='velocepay',
                )
                
                # Create order items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        transaction=new_transaction,
                        product=cart_item.product,
                        product_name=cart_item.product.name,
                        product_price=cart_item.product.price,
                        quantity=cart_item.quantity,
                        size=cart_item.size,
                    )
                
                # Clear the cart
                cart_items.delete()
                
                # Clear checkout data from session
                if 'checkout_data' in request.session:
                    del request.session['checkout_data']
                
                # Generate mock VelocePay payment URL
                payment_url = generate_velocepay_url(new_transaction)
                new_transaction.payment_url = payment_url
                new_transaction.save()
                
                return redirect('transaction:success', transaction_id=transaction_id)
                
        except Exception as e:
            messages.error(request, f"Error processing your order: {str(e)}")
            return redirect('transaction:checkout')
    
    context = {
        'cart_items': cart_items,
        'product_total': product_total,
        'delivery_price': delivery_price,
        'transaction_amount': transaction_amount,
        'checkout_data': checkout_data,
    }
    
    return render(request, 'checkout_confirm.html', context)

def generate_velocepay_url(transaction_obj):
    """
    Generate a mock VelocePay URL
    In a real implementation, this would call the VelocePay API
    """
    # Create a mock URL with the transaction ID as a parameter
    base_url = reverse('transaction:process_payment', args=[transaction_obj.transaction_id])
    
    # In a real implementation, this would include authentication tokens, etc.
    return base_url

@login_required(login_url='users:login')
def process_payment(request, transaction_id):
    """
    Process the payment from VelocePay
    In a real implementation, this would be a callback from the payment processor
    """
    try:
        txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
        
        if txn.status != 'pending':
            messages.warning(request, "This order has already been processed.")
            return redirect('transaction:order_detail', transaction_id=transaction_id)
        
        with transaction.atomic():
            # Update transaction status
            txn.status = 'processing'
            txn.save()
            
            # Update stock
            for item in txn.items.all():
                product_size = ProductSize.objects.select_for_update().get(
                    product=item.product,
                    size=item.size
                )
                
                # Reduce stock
                product_size.stock -= item.quantity
                product_size.save()
        
        messages.success(request, "Pembayaran berhasil! Pesanan Anda sedang diproses.")
        return redirect('transaction:order_detail', transaction_id=transaction_id)
        
    except Exception as e:
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('transaction:order_history')

@login_required(login_url='users:login')
def transaction_success(request, transaction_id):
    """Success page after completing an order"""
    try:
        transaction_obj = Transaction.objects.get(transaction_id=transaction_id, user=request.user)
    except Transaction.DoesNotExist:
        raise Http404("Transaction not found")
    
    context = {
        'transaction': transaction_obj,
    }
    
    return render(request, 'success.html', context)

@login_required(login_url='users:login')
def order_history(request):
    """Displays user's order history"""
    # Get all user transactions ordered by date (newest first)
    transactions = Transaction.objects.filter(user=request.user).order_by('-date_created')
    
    context = {
        'transactions': transactions,
    }
    
    return render(request, 'order_history.html', context)

@login_required(login_url='users:login')
def order_detail(request, transaction_id):
    """Displays details of a specific order"""
    try:
        transaction_obj = Transaction.objects.get(transaction_id=transaction_id, user=request.user)
    except Transaction.DoesNotExist:
        raise Http404("Order not found")
    
    # Get order items
    order_items = transaction_obj.items.all()
    
    context = {
        'transaction': transaction_obj,
        'order_items': order_items,
    }
    
    return render(request, 'order_detail.html', context)
