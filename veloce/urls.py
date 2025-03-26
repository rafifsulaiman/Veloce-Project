from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('homepage.urls'))  # Cara 1: Root domain ke homepage
    path('homepage/', include('homepage.urls')),    # Nanti kalau diakses '/', ke homepage.urls
    path('', include('main.urls')),
]
