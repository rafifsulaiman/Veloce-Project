import time
import logging
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout

logger = logging.getLogger(__name__)

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.session_expire_seconds = getattr(settings, 'SESSION_EXPIRE_SECONDS', 1800)
        logger.debug("AutoLogoutMiddleware aktif dengan SESSION_EXPIRE_SECONDS = %s", self.session_expire_seconds)

    def __call__(self, request):
        if request.user.is_authenticated:
            session_key = request.session.session_key  # Ambil session key untuk logging
            logger.debug("Current session key: %s", session_key)
            
            last_activity = request.session.get('last_activity')
            now = time.time()
            if last_activity:
                elapsed = now - last_activity
                logger.debug("User %s aktif selama %s detik (session key: %s)", request.user.username, elapsed, session_key)
                if elapsed > self.session_expire_seconds:
                    logger.info("Session expired untuk user: %s (session key: %s)", request.user.username, session_key)
                    
                    # Simpan session key sebelum logout untuk validasi
                    current_session_key = request.session.session_key
                    logger.debug("Session key sebelum logout: %s", current_session_key)
                    
                    # Lakukan logout (session akan di-flush)
                    logout(request)
                    
                    # Validasi session setelah logout (harus None)
                    if request.session.session_key is None:
                        logger.debug("Session telah di-flush, session key: None")
                    else:
                        logger.warning("Session masih ada setelah logout, session key: %s", request.session.session_key)
                    
                    # Redirect dan hapus cookie session
                    response = redirect('home:index')
                    response.delete_cookie(settings.SESSION_COOKIE_NAME)
                    return response
            request.session['last_activity'] = now

        response = self.get_response(request)
        return response
