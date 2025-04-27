from django.shortcuts import render
from products.models import Product

def index(request):
    """
    Main homepage view accessible to all users (guest, authenticated, and admin)
    """
    featured_products = Product.objects.all()[:4]
    
    # Features for different user types
    guest_features = [
        {
            'title': 'Browse Products',
            'description': 'Explore our premium footwear collection with various styles and sizes.',
            'icon': 'fas fa-search',
            'url': '/catalog/',
            'color': 'bg-blue-100'
        },
        {
            'title': 'Create Account',
            'description': 'Register to gain access to exclusive features and discounts.',
            'icon': 'fas fa-user-plus',
            'url': '/users/register/',
            'color': 'bg-green-100'
        },
        {
            'title': 'Easy Navigation',
            'description': 'Find your perfect pair with our intuitive filtering system.',
            'icon': 'fas fa-filter',
            'url': '/catalog/',
            'color': 'bg-yellow-100'
        }
    ]
    
    user_features = [
        {
            'title': 'Shopping Cart',
            'description': 'Add items to your cart and complete your purchase seamlessly.',
            'icon': 'fas fa-shopping-cart',
            'url': '/cart/',
            'color': 'bg-purple-100'
        },
        {
            'title': 'Order History',
            'description': 'Track and manage your past and current orders.',
            'icon': 'fas fa-history',
            'url': '/transaction/orders/',
            'color': 'bg-indigo-100'
        },
        {
            'title': 'Address Management',
            'description': 'Manage your shipping addresses for faster checkout.',
            'icon': 'fas fa-map-marker-alt',
            'url': '/users/profile/addresses/',
            'color': 'bg-red-100'
        },
        {
            'title': 'Profile Settings',
            'description': 'Update your personal information and account preferences.',
            'icon': 'fas fa-user-cog',
            'url': '/users/profile/',
            'color': 'bg-teal-100'
        }
    ]
    
    admin_features = [
        {
            'title': 'Product Management',
            'description': 'Add, edit, and delete products in the catalog.',
            'icon': 'fas fa-boxes',
            'url': '/admindashboard/admin-page/',
            'color': 'bg-orange-100'
        },
        {
            'title': 'Transaction Management',
            'description': 'Process and manage customer orders and transactions.',
            'icon': 'fas fa-exchange-alt',
            'url': '/admindashboard/admin-transaction-list/',
            'color': 'bg-pink-100'
        },
        {
            'title': 'Audit Logs',
            'description': 'View activity logs for administrative actions.',
            'icon': 'fas fa-clipboard-list',
            'url': '/admindashboard/admin-audit-logs/',
            'color': 'bg-blue-100'
        },
        {
            'title': 'Product Audit Logs',
            'description': 'Monitor specific product-related activities.',
            'icon': 'fas fa-tasks',
            'url': '/admindashboard/admin-product-audit-logs/',
            'color': 'bg-green-100'
        }
    ]
    
    context = {
        'featured_products': featured_products,
        'guest_features': guest_features,
    }
    
    if request.user.is_authenticated:
        if request.user.is_staff:
            context["user_type"] = "admin"
            context["features"] = admin_features
        else:
            context["user_type"] = "user"
            context["features"] = user_features
    else:
        context["user_type"] = "guest"
        context["features"] = guest_features
    
    return render(request, 'main.html', context)
