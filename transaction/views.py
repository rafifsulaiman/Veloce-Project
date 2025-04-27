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
from django.contrib.admin.views.decorators import staff_member_required

from cart.models import CartItem
from products.models import Product, ProductSize
from .models import Transaction, OrderItem, AuditLog
from .forms import CheckoutForm
from users.models import Address

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
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            address_obj = form.cleaned_data['address']
            # Store form data in session for confirmation step
            request.session['checkout_data'] = {
                'address_id': address_obj.id,
                'payment_method': form.cleaned_data['payment_method'],
            }
            return redirect('transaction:checkout_confirm')
    else:
        form = CheckoutForm(user=request.user)
    
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
    
    # Get the selected address object
    address_obj = None
    if 'address_id' in checkout_data:
        try:
            address_obj = Address.objects.get(id=checkout_data['address_id'], user=request.user)
        except Address.DoesNotExist:
            messages.error(request, "Selected address not found.")
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
                # Check stock availability one last time and decrease stock
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
                    # Decrease stock
                    product_size.stock -= cart_item.quantity
                    product_size.save()
                # Create transaction with fields based on ER diagram
                transaction_id = f"TRX-{uuid.uuid4().hex[:12].upper()}"
                new_transaction = Transaction.objects.create(
                    transaction_id=transaction_id,
                    user=request.user,
                    status='pending',
                    transaction_amount=transaction_amount,
                    delivery_price=delivery_price,
                    shipping_address=address_obj.get_full_address_en() if address_obj else '',
                    shipping_city=address_obj.city if address_obj else '',
                    shipping_postal_code=address_obj.postal_code if address_obj else '',
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
    # TODO: Restore stock if order is cancelled or expires
    
    context = {
        'cart_items': cart_items,
        'product_total': product_total,
        'delivery_price': delivery_price,
        'transaction_amount': transaction_amount,
        'checkout_data': checkout_data,
        'address_obj': address_obj,
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

@login_required
@transaction.atomic
def cancel_order(request, transaction_id):
    """Allow users to cancel their own pending orders."""
    # Untuk user biasa, cek pesanan miliknya sendiri
    if not request.user.is_staff:
        txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    else:
        # Admin bisa membatalkan pesanan siapa saja
        txn = get_object_or_404(Transaction, transaction_id=transaction_id)
    
    # Cek apakah pesanan sudah dibatalkan
    if txn.status == 'cancelled':
        messages.warning(request, "This order has already been cancelled.")
        if request.user.is_staff:
            return redirect('admindashboard:admin_transaction_detail', transaction_id=transaction_id)
        return redirect('transaction:order_detail', transaction_id=transaction_id)
    
    # Only allow cancellation of pending orders
    if txn.status != 'pending':
        messages.warning(request, "Only pending orders can be cancelled.")
        if request.user.is_staff:
            return redirect('admindashboard:admin_transaction_detail', transaction_id=transaction_id)
        return redirect('transaction:order_detail', transaction_id=transaction_id)
    
    # Restore stock for each item
    for item in txn.items.all():
        product_size = ProductSize.objects.select_for_update().get(
            product=item.product,
            size=item.size
        )
        product_size.stock += item.quantity
        product_size.save()
    
    txn.status = 'cancelled'
    txn.shipping_status = 'cancelled'
    txn.save()
    
    messages.success(request, "The order has been cancelled and stock has been restored.")
    
    # Redirect ke tempat yang sesuai berdasarkan jenis pengguna
    if request.user.is_staff:
        return redirect('admindashboard:admin_transaction_list')
    return redirect('transaction:order_history')
