from django.shortcuts import render
from products.models import Product

def index(request):
    """
    Main homepage view accessible to all users (guest, authenticated, and admin)
    """
    featured_products = Product.objects.all()[:4]
    
    context = {
        'featured_products': featured_products
    }
    
    if request.user.is_authenticated:
        context["is_admin"] = request.user.is_staff
    
    return render(request, 'main.html', context)
