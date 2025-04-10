from django.shortcuts import render
from products.models import Product

def index(request):
    """
    Main homepage view accessible to all users (guest, authenticated, and admin)
    """
    # Get a few products to showcase in the home page
    featured_products = Product.objects.all()[:4]
    
    context = {
        'featured_products': featured_products
    }
    
    # Add user-specific info to context if authenticated
    if request.user.is_authenticated:
        context["is_admin"] = request.user.is_staff
    
    return render(request, 'home/main.html', context)
