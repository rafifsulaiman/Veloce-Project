from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # If already logged in, do nothing
        if request.user.is_authenticated:
            return

        # Pull the Google-verified email
        email = sociallogin.account.extra_data.get('email')
        if not email:
            # fallback—let allauth continue (will likely fail later)
            return

        email = email.lower()
        # If we don’t have a matching user, redirect to signup
        if not User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email has not been registered.')
            raise ImmediateHttpResponse(redirect('users:register'))

        # Otherwise, connect the sociallogin to that existing user
        # (and allauth will log them in)
        if not sociallogin.is_existing:
            user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, user)