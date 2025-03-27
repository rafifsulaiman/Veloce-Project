from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('homepage.urls'))  # Cara 1: Root domain ke homepage
    path('homepage/', include('homepage.urls')),    # Nanti kalau diakses '/', ke homepage.urls
    path('', include('main.urls')),
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'))),
]
