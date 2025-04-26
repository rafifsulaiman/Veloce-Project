from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm, UserRegisterForm, UserLoginForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Address
from django.conf import settings
import logging
from django_ratelimit.decorators import ratelimit
from captcha.image import ImageCaptcha
from io import BytesIO
import random
import string
from PIL import Image
import base64
import re
from django.utils.html import strip_tags
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# Create your views here.
logger = logging.getLogger(__name__)
@ratelimit(key='user_or_ip', rate='10/m', block=True)
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

@ratelimit(key='user_or_ip', rate='10/m', block=True)
def user_login(request):
    # Siapkan form login
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        
        # Hitung gagal login dari session
        failed_attempts = request.session.get('failed_login_attempts', 0)
        
        # Jika sudah gagal >= 3 kali, wajib isi captcha
        if failed_attempts >= 3:
            input_captcha = request.POST.get('captcha_text')
            correct_captcha = request.session.get('captcha_text')
            
            if not input_captcha or input_captcha.lower() != correct_captcha.lower():
                messages.error(request, 'Incorrect CAPTCHA.')
                # regenerate captcha
                return _render_login_with_captcha(request, form)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                request.session['failed_login_attempts'] = 0  # Reset counter
                messages.success(request, f'Welcome, {username}!')
                return redirect('home:index')
            else:
                messages.error(request, 'Invalid username or password.')
                request.session['failed_login_attempts'] = failed_attempts + 1
                
                if request.session['failed_login_attempts'] >= 3:
                    return _render_login_with_captcha(request, form)

    else:
        form = UserLoginForm()
        # Reset captcha-related session if fresh GET
        request.session.pop('captcha_text', None)

    return render(request, 'login.html', {'form': form})

def _render_login_with_captcha(request, form):
    # Generate Captcha Text
    text = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    request.session['captcha_text'] = text

    # Generate Captcha Image
    captcha = ImageCaptcha(width=280, height=90)
    data = captcha.generate(text)
    image = Image.open(data)

    # Convert image to base64 to embed in HTML
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    captcha_base64 = base64.b64encode(buffered.getvalue()).decode()

    context = {
        'form': form,
        'captcha_image': captcha_base64,
    }
    return render(request, 'login.html', context)

@login_required(login_url='users:login')
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

@login_required(login_url='users:login')
@ratelimit(key='user_or_ip', rate='10/m', block=True)
def profile_view(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'profile/profile.html', context)

NAME_REGEX = re.compile(r'^[\w\s\-]+$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-]+$')
url_validator = URLValidator()
@login_required(login_url='users:login')
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        # Update user data
        raw_first = strip_tags(request.POST.get('first_name', '')).strip()
        raw_last  = strip_tags(request.POST.get('last_name', '')).strip()
        raw_phone = strip_tags(request.POST.get('phone_number', '')).strip()
        raw_url   = strip_tags(request.POST.get('profile_pic_url', '')).strip()
        gender    = request.POST.get('gender')

        # Validasi first_name
        if raw_first and not NAME_REGEX.match(raw_first):
            messages.error(request, 'First name mengandung karakter tidak valid.')
            return redirect('users:edit_profile')
        # Validasi last_name
        if raw_last and not NAME_REGEX.match(raw_last):
            messages.error(request, 'Last name mengandung karakter tidak valid.')
            return redirect('users:edit_profile')
        # Validasi phone_number
        if raw_phone and not PHONE_REGEX.match(raw_phone):
            messages.error(request, 'Phone number mengandung karakter tidak valid.')
            return redirect('users:edit_profile')
        # Validasi profile_pic_url
        if raw_url is not None and raw_url != 'None':
            try:
                url_validator(raw_url)
            except ValidationError:
                messages.error(request, 'Profile picture URL tidak valid.')
                return redirect('users:edit_profile')

        # Assign ke model jika lolos validasi
        if raw_first:
            user.first_name = raw_first
        if raw_last:
            user.last_name = raw_last
        if raw_phone:
            user.phone_number = raw_phone
        if gender:
            user.gender = gender
        if raw_url:
            user.profile_pic_url = raw_url
        
        user.save()
        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('users:profile')
    
    context = {
        'user': user
    }
    return render(request, 'profile/edit_profile.html', context)

@login_required(login_url='users:login')
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    context = {
        'addresses': addresses
    }
    return render(request, 'profile/address_list.html', context)

@login_required(login_url='users:login')
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

@login_required(login_url='users:login')
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
