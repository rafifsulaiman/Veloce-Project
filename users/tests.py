# users/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.cache import cache
from users.models import CustomUser, Address

User = get_user_model()

@override_settings(RATELIMIT_ENABLE=True)
class UserViewsTest(TestCase):
    def setUp(self):
        # clear any ratelimit counters before each test
        cache.clear()

        self.client = Client()
        self.username = "testuser"
        self.password = "password123"
        self.user = User.objects.create_user(
            username=self.username,
            email="test@example.com",
            password=self.password
        )

    def test_register_view_get(self):
        resp = self.client.get(reverse('users:register'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'register.html')

    def test_register_view_post_success(self):
        data = {
            'username': 'alice',
            'first_name': 'Alice',
            'last_name': 'Smith',
            'email': 'alice@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        resp = self.client.post(reverse('users:register'), data)
        self.assertRedirects(resp, reverse('users:login'))
        self.assertTrue(User.objects.filter(username='alice').exists())

    def test_register_view_post_invalid_email(self):
        data = {
            'username': 'bob',
            'first_name': 'Bob',
            'last_name': 'Builder',
            'email': 'not-an-email',
            'password1': 'pass1234',
            'password2': 'pass1234'
        }
        resp = self.client.post(reverse('users:register'), data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)
        self.assertTrue(resp.context['form'].errors)
        self.assertIn('email', resp.context['form'].errors)
        self.assertEqual(
            resp.context['form'].errors['email'][0],
            "Format email tidak valid. Contoh: user@example.com"
        )

    def test_login_success_and_reset_fail_count(self):
        # failed_login_attempts was reset in setUp; here we simulate 2 prior fails
        session = self.client.session
        session['failed_login_attempts'] = 2
        session.save()

        resp = self.client.post(reverse('users:login'), {
            'username': self.username,
            'password': self.password
        })
        self.assertRedirects(resp, reverse('home:index'))
        self.assertEqual(self.client.session.get('failed_login_attempts'), 0)

    def test_login_invalid_credentials_increment_fail_count(self):
        session = self.client.session
        session['failed_login_attempts'] = 2
        session.save()

        resp = self.client.post(reverse('users:login'), {
            'username': 'wrong',
            'password': 'wrong'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Invalid username or password.")
        self.assertEqual(self.client.session.get('failed_login_attempts'), 3)

    def test_captcha_required_after_3_fails(self):
        session = self.client.session
        session['failed_login_attempts'] = 3
        session['captcha_text'] = 'ABC12'
        session.save()

        resp = self.client.post(reverse('users:login'), {
            'username': self.username,
            'password': self.password,
            'captcha_text': 'WRONG'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Incorrect CAPTCHA.')

    def test_captcha_cleared_on_get(self):
        session = self.client.session
        session['captcha_text'] = 'TOBEDELETED'
        session.save()

        self.client.get(reverse('users:login'))
        self.assertNotIn('captcha_text', self.client.session)

    def test_profile_view_requires_login(self):
        url = reverse('users:profile')
        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

    def test_profile_view_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(reverse('users:profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'profile/profile.html')

    def test_edit_profile(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('users:edit_profile'), {
            'first_name': 'Rafi',
            'last_name' : 'Test',
            'phone_number': '081234567890',
            'profile_pic_url': 'http://example.com/pic.png',
            'gender': 'Male',
        })
        self.assertRedirects(resp, reverse('users:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Rafi')
        self.assertEqual(self.user.last_name,  'Test')
        self.assertEqual(self.user.phone_number, '081234567890')
        self.assertEqual(self.user.profile_pic_url, 'http://example.com/pic.png')
        self.assertEqual(self.user.gender, 'Male')

    def test_logout_clears_session_and_cookie(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(reverse('users:logout'))
        self.assertRedirects(resp, reverse('home:index'))
        msgs = list(get_messages(resp.wsgi_request))
        self.assertTrue(any("logged out" in str(m).lower() for m in msgs))

    # ----- Address views -----

    def test_address_list_requires_login(self):
        url = reverse('users:addresses')
        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

    def test_address_list_and_context(self):
        Address.objects.create(
            user=self.user, name='Home',
            phone_number='08123',
            street_address='Jl. A', rt_rw='01/02',
            village='Desa', district='Kec',
            city='Kota', province='Prov',
            postal_code='12345', additional_info='', is_main=True
        )
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(reverse('users:addresses'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'profile/address_list.html')
        self.assertEqual(len(resp.context['addresses']), 1)

    def test_add_address_get_and_post(self):
        url = reverse('users:add_address')
        # requires login
        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'profile/add_address.html')

        data = {
            'name': 'Office', 'phone_number': '08999',
            'street_address': 'Jl. B', 'rt_rw': '03/04',
            'village': 'DesaB', 'district': 'KecB',
            'city': 'KotaB', 'province': 'ProvB',
            'postal_code': '54321', 'additional_info': '2nd floor',
            'is_main': 'Yes'
        }
        resp = self.client.post(url, data)
        self.assertRedirects(resp, reverse('users:addresses'))
        self.assertEqual(Address.objects.filter(user=self.user).count(), 1)

    def test_edit_address_get_and_post(self):
        addr = Address.objects.create(
            user=self.user, name='X',
            phone_number='08000',
            street_address='Jl. X', rt_rw='05/06',
            village='DesaX', district='KecX',
            city='KotaX', province='ProvX',
            postal_code='00000', additional_info='', is_main=False
        )
        url = reverse('users:edit_address', args=[addr.id])

        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'profile/edit_address.html')

        data = {
            'name': 'Y', 'phone_number': '08111',
            'street_address': 'Jl. Y', 'rt_rw': '07/08',
            'village': 'DesaY', 'district': 'KecY',
            'city': 'KotaY', 'province': 'ProvY',
            'postal_code': '11111', 'additional_info': 'near park',
            'is_main': 'Yes'
        }
        resp = self.client.post(url, data)
        self.assertRedirects(resp, reverse('users:addresses'))
        addr.refresh_from_db()
        self.assertEqual(addr.name, 'Y')
        self.assertTrue(addr.is_main)

    # ----- Timer page -----

    def test_timer_page(self):
        url = reverse('users:timer_page')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'timer.html')

    # ----- Rate‐limit enforcement -----

    def test_rate_limit_enforced(self):
        # Make 10 rapid requests; all should pass
        for _ in range(10):
            resp = self.client.get(reverse('users:register'))
            self.assertEqual(resp.status_code, 200)

        # 11th request should be blocked by ratelimit
        resp = self.client.get(reverse('users:register'))
        self.assertIn(resp.status_code, (403, 429))
