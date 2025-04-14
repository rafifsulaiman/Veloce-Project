from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm, UserRegisterForm, UserLoginForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Address
from django.conf import settings
import logging

# Create your views here.
logger = logging.getLogger(__name__)
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('users:login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome, {username}!')
                return redirect('home:index')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

@login_required
def user_logout(request):
    # Simpan session key sebelum logout untuk keperluan validasi/log
    current_session_key = request.session.session_key
    if current_session_key:
        logger.debug("Session key sebelum logout: %s", current_session_key)
    else:
        logger.debug("Tidak ada session key sebelum logout (mungkin sudah expired)")

    # Lakukan logout (session akan di-flush)
    logout(request)
    
    # Setelah logout, session di-flush sehingga session key akan None atau berbeda
    if request.session.session_key is None:
        logger.debug("Session key setelah logout: None (session telah di-flush)")
    else:
        logger.warning("Session key setelah logout masih ada: %s", request.session.session_key)
    
    messages.success(request, 'You have been logged out.')
    response = redirect('home:index')
    
    # Hapus cookie session secara eksplisit (default cookie: 'sessionid' kecuali Anda menyetel SESSION_COOKIE_NAME)
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    
    logger.debug("User logged out and session cookie deleted. Session key sebelum logout: %s", current_session_key)
    return response

@login_required
def profile_view(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'profile/profile.html', context)

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        # Update user data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        gender = request.POST.get('gender')
        profile_pic_url = request.POST.get('profile_pic_url')
        
        # Only update if values provided
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            user.email = email
        if phone_number:
            user.phone_number = phone_number
        if gender:
            user.gender = gender
        if profile_pic_url:
            user.profile_pic_url = profile_pic_url
        
        user.save()
        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('users:profile')
    
    context = {
        'user': user
    }
    return render(request, 'profile/edit_profile.html', context)

@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    context = {
        'addresses': addresses
    }
    return render(request, 'profile/address_list.html', context)

@login_required
def add_address(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        street_address = request.POST.get('street_address')
        rt_rw = request.POST.get('rt_rw')
        village = request.POST.get('village')
        district = request.POST.get('district')
        city = request.POST.get('city')
        province = request.POST.get('province')
        postal_code = request.POST.get('postal_code')
        additional_info = request.POST.get('additional_info')
        is_main = request.POST.get('is_main') == 'Yes'
        
        # Create new address
        new_address = Address(
            user=request.user,
            name=name,
            phone_number=phone_number,
            street_address=street_address,
            rt_rw=rt_rw,
            village=village,
            district=district,
            city=city,
            province=province,
            postal_code=postal_code,
            additional_info=additional_info,
            is_main=is_main
        )
        new_address.save()
        
        messages.success(request, 'Alamat baru berhasil ditambahkan.')
        return redirect('users:addresses')
    
    return render(request, 'profile/add_address.html')

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        street_address = request.POST.get('street_address')
        rt_rw = request.POST.get('rt_rw')
        village = request.POST.get('village')
        district = request.POST.get('district')
        city = request.POST.get('city')
        province = request.POST.get('province')
        postal_code = request.POST.get('postal_code')
        additional_info = request.POST.get('additional_info')
        is_main = request.POST.get('is_main') == 'Yes'
        
        # Update address
        address.name = name
        address.phone_number = phone_number
        address.street_address = street_address
        address.rt_rw = rt_rw
        address.village = village
        address.district = district
        address.city = city
        address.province = province
        address.postal_code = postal_code
        address.additional_info = additional_info
        address.is_main = is_main
        address.save()
        
        messages.success(request, 'Alamat berhasil diperbarui.')
        return redirect('users:addresses')
    
    context = {
        'address': address
    }
    return render(request, 'profile/edit_address.html', context)

def timer_page(request):
    return render(request, 'timer.html')
