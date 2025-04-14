from django.shortcuts import render, redirect, get_object_or_404
from admindashboard.forms import ProductForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from products.models import Product
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum
from transaction.models import Transaction, AuditLog, OrderItem
from datetime import datetime, timedelta

@login_required
def admin_page(request):
    if not request.user.is_staff:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('products:catalog')
    
    # Get base queryset
    products = Product.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(product_id__icontains=search_query) |
            Q(brand__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products, 15)  # Show 15 products per page
    page_number = request.GET.get('page', 1)
    products_page = paginator.get_page(page_number)
    
    # Get statistics for admin dashboard
    total_stock = sum([size.stock for product in Product.objects.all() for size in product.sizes.all()])
    brands_count = Product.objects.values('brand').distinct().count()
    sizes_count = set([size.size for product in Product.objects.all() for size in product.sizes.all()])
    
    context = {
        'products': products_page,
        'total_stock': total_stock,
        'brands_count': brands_count,
        'sizes_count': len(sizes_count)
    }
    
    return render(request, 'admin_page.html', context)
    
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
    return render(request, 'add_product.html', {'form': form})

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
@login_required
def delete_product(request, product_id):
    if not request.user.is_staff:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('products:catalog')
    
    product = get_object_or_404(Product, product_id=product_id)
    product.delete()
    messages.success(request, f"Produk {product.name} berhasil dihapus.")
    return redirect('admindashboard:admin_page')

# Admin transaction management views
@staff_member_required
def admin_transaction_list(request):
    """
    Admin view to list and manage all transactions
    This follows the UML sequence diagram where admin opens 'Manage Transactions' page
    """
    # Log the access attempt
    log_admin_action(request, action='view', details='Admin accessed transaction list')
    
    # Get filter parameters
    status = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    search_query = request.GET.get('query', '')
    
    # Base queryset
    transactions = Transaction.objects.all().order_by('-date_created')
    
    # Apply filters
    if status:
        transactions = transactions.filter(status=status)
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
            transactions = transactions.filter(date_created__range=[start, end])
        except ValueError:
            # Invalid date format, ignore the filter
            pass
    
    if search_query:
        transactions = transactions.filter(
            Q(transaction_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(shipping_city__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(transactions, 20)  # Show 20 transactions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_status': status,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'filter_query': search_query,
        'status_choices': Transaction.PAYMENT_STATUS_CHOICES,
        'shipping_status_choices': Transaction.SHIPPING_STATUS_CHOICES,
    }
    
    return render(request, 'transaction_list.html', context)

@staff_member_required
def admin_transaction_detail(request, transaction_id):
    """
    Admin view to see details of a specific transaction
    """
    try:
        transaction_obj = Transaction.objects.get(transaction_id=transaction_id)
        
        # Log the access
        log_admin_action(
            request, 
            action='view', 
            transaction=transaction_obj,
            details=f'Admin viewed transaction {transaction_id}'
        )
        
        # Get order items
        order_items = transaction_obj.items.all()
        
        # Get audit logs for this transaction
        audit_logs = AuditLog.objects.filter(transaction=transaction_obj)
        
        context = {
            'transaction': transaction_obj,
            'order_items': order_items,
            'audit_logs': audit_logs,
            'status_choices': Transaction.PAYMENT_STATUS_CHOICES,
            'shipping_status_choices': Transaction.SHIPPING_STATUS_CHOICES,
        }
        
        return render(request, 'transaction_detail.html', context)
    
    except Transaction.DoesNotExist:
        # Log unauthorized or suspicious access attempt
        log_admin_action(
            request, 
            action='unauthorized',
            details=f'Attempted to access non-existent transaction {transaction_id}'
        )
        messages.error(request, "Transaction not found.")
        return redirect('admindashboard:admin_transaction_list')

@staff_member_required
def admin_update_transaction_status(request, transaction_id):
    """
    Admin view to update transaction status (payment and shipping)
    This implements the status change functionality in the UML diagram
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)
    
    try:
        transaction_obj = Transaction.objects.get(transaction_id=transaction_id)
        
        # Get the new status values
        payment_status = request.POST.get('payment_status')
        shipping_status = request.POST.get('shipping_status')
        
        # Validate RBAC (Role-Based Access Control)
        # Here we could implement more fine-grained access control
        # For example, check if the admin has specific permissions to change status
        if not verify_admin_access_rights(request.user, 'change_transaction_status'):
            # Log unauthorized access attempt
            log_admin_action(
                request, 
                action='unauthorized',
                transaction=transaction_obj,
                details=f'Unauthorized attempt to change status of transaction {transaction_id}'
            )
            return JsonResponse({
                'status': 'error', 
                'message': 'You do not have permission to perform this action'
            }, status=403)
        
        # Record old status for audit
        old_payment_status = transaction_obj.status
        old_shipping_status = transaction_obj.shipping_status
        
        # Update transaction status
        status_changed = False
        
        if payment_status and payment_status in dict(Transaction.PAYMENT_STATUS_CHOICES):
            transaction_obj.status = payment_status
            status_changed = True
        
        if shipping_status and shipping_status in dict(Transaction.SHIPPING_STATUS_CHOICES):
            transaction_obj.shipping_status = shipping_status
            status_changed = True
        
        if status_changed:
            transaction_obj.save()
            
            # Log the status change
            details = f'Changed payment status from {old_payment_status} to {transaction_obj.status}. '
            details += f'Changed shipping status from {old_shipping_status} to {transaction_obj.shipping_status}.'
            
            log_admin_action(
                request, 
                action='status_change',
                transaction=transaction_obj,
                details=details
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Transaction status updated successfully',
                'new_payment_status': transaction_obj.get_status_display(),
                'new_shipping_status': transaction_obj.get_shipping_status_display()
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'No valid status changes provided'}, status=400)
            
    except Transaction.DoesNotExist:
        # Log suspicious activity
        log_admin_action(
            request, 
            action='suspicious',
            details=f'Attempted to update non-existent transaction {transaction_id}'
        )
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)

@staff_member_required
def admin_cancel_transaction(request, transaction_id):
    """
    Admin view to cancel a transaction
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)
    
    try:
        transaction_obj = Transaction.objects.get(transaction_id=transaction_id)
        
        # Validate RBAC
        if not verify_admin_access_rights(request.user, 'cancel_transaction'):
            # Log unauthorized access
            log_admin_action(
                request, 
                action='unauthorized',
                transaction=transaction_obj,
                details=f'Unauthorized attempt to cancel transaction {transaction_id}'
            )
            return JsonResponse({
                'status': 'error', 
                'message': 'You do not have permission to cancel transactions'
            }, status=403)
        
        # Record old status for audit
        old_payment_status = transaction_obj.status
        old_shipping_status = transaction_obj.shipping_status
        
        # Cancel the transaction
        transaction_obj.status = 'cancelled'
        transaction_obj.shipping_status = 'cancelled'
        transaction_obj.save()
        
        # Log the cancellation
        log_admin_action(
            request, 
            action='cancel',
            transaction=transaction_obj,
            details=f'Cancelled transaction. Previous payment status: {old_payment_status}, Previous shipping status: {old_shipping_status}'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Transaction cancelled successfully'
        })
        
    except Transaction.DoesNotExist:
        # Log suspicious activity
        log_admin_action(
            request, 
            action='suspicious',
            details=f'Attempted to cancel non-existent transaction {transaction_id}'
        )
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)

@staff_member_required
def admin_audit_logs(request):
    """
    Admin view to see all audit logs
    """
    # Verify access rights for viewing audit logs
    if not verify_admin_access_rights(request.user, 'view_audit_logs'):
        messages.error(request, "You do not have permission to view audit logs.")
        return redirect('admindashboard:admin_transaction_list')
    
    # Get filter parameters
    action_type = request.GET.get('action', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    admin_filter = request.GET.get('admin', '')
    
    # Base queryset
    logs = AuditLog.objects.all()
    
    # Apply filters
    if action_type:
        logs = logs.filter(action=action_type)
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            logs = logs.filter(timestamp__range=[start, end])
        except ValueError:
            # Invalid date format, ignore the filter
            pass
    
    if admin_filter:
        logs = logs.filter(admin_user__username=admin_filter)
    
    # Pagination
    paginator = Paginator(logs, 50)  # Show 50 logs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all admin users for the filter dropdown
    admin_users = set(AuditLog.objects.values_list('admin_user__username', flat=True).distinct())
    
    context = {
        'page_obj': page_obj,
        'filter_action': action_type,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'filter_admin': admin_filter,
        'admin_users': admin_users,
        'action_choices': AuditLog.ACTION_CHOICES,
    }
    
    return render(request, 'audit_logs.html', context)

# Helper functions for admin transaction management

def log_admin_action(request, action, transaction=None, details=None):
    """
    Helper function to log admin actions
    """
    # Create the audit log entry
    log_entry = AuditLog(
        admin_user=request.user,
        transaction=transaction,
        action=action,
        details=details,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    log_entry.save()
    return log_entry

def get_client_ip(request):
    """
    Helper function to get the client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def verify_admin_access_rights(user, permission_key):
    """
    Helper function to verify admin's RBAC permissions
    In a real implementation, this would check against a more sophisticated 
    permission system, but for this example, we'll use Django's built-in permissions
    """
    # All staff users can view transactions
    if permission_key == 'view_transactions':
        return user.is_staff
        
    # For more sensitive operations, we require specific permissions
    permission_mapping = {
        'change_transaction_status': 'transaction.change_transaction',
        'cancel_transaction': 'transaction.delete_transaction',
        'view_audit_logs': 'transaction.view_auditlog',
    }
    
    django_permission = permission_mapping.get(permission_key)
    if django_permission:
        return user.has_perm(django_permission)
    
    # If no mapping is found, deny access by default
    return False