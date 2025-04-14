from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if request.user.is_authenticated:
            return

        # Debug: print data dari sociallogin
        email_address = sociallogin.account.extra_data.get('email')
        if not email_address:
            return

        # Normalisasi email misalnya dengan mengkonversi ke lowercase
        email_address = email_address.lower()

        try:
            user = User.objects.get(email__iexact=email_address)
        except User.DoesNotExist:
            # Tidak ada user dengan email ini, lanjutkan ke signup
            return

        # Jika sudah terhubung, tidak perlu mengubah
        if sociallogin.is_existing:
            return

        # Lakukan koneksi akun sosial dengan akun yang sudah ada
        sociallogin.connect(request, user)
