"""
WSGI config for veloce project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application
import os

load_dotenv()

# Now you can access environment variables
SECRET_KEY = os.getenv('SECRET_KEY')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "veloce.settings")

application = get_wsgi_application()
