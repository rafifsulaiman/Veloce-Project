from django.urls import path
from .views import register, user_login, user_logout, profile_view, edit_profile, address_list, add_address, edit_address, timer_page

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/addresses/', address_list, name='addresses'),
    path('profile/addresses/add/', add_address, name='add_address'),
    path('profile/addresses/edit/<int:address_id>/', edit_address, name='edit_address'),
    path('timer/', timer_page, name='timer_page'),
] 