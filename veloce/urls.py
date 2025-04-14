from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('users/', include('users.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('transaction/', include('transaction.urls')),
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'))),
    path('admindashboard/', include('admindashboard.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path("accounts/", include("allauth.urls")),
]
