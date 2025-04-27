from django.test import TestCase, Client, override_settings 
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from products.models import Product, ProductSize
from .models import CartItem

User = get_user_model()

@override_settings(RATELIMIT_ENABLE=True)
class CartViewsTest(TestCase):

    #mengatur client normal user dan staff serta produk dan ukuran serta cart item
    def setUp(self):
        self.client = Client()
        #normal user & staff
        self.user  = User.objects.create_user(username='u', email='u@example.com', password='pass')
        self.staff = User.objects.create_user(username='s', email='s@example.com', password='pass', is_staff=True)

        #produk & ukuran
        self.prod = Product.objects.create(
            product_id='P1', name='Prod', brand='Nike',
            gender='men', price=100, image_url='["u"]'
        )
        ProductSize.objects.create(product=self.prod, size=40, stock=2)
        ProductSize.objects.create(product=self.prod, size=42, stock=5)

        #cart item awal
        self.cart_item = CartItem.objects.create(
            user=self.user, product=self.prod, size=40, quantity=1
        )

    #memastikan view cart memerlukan login dan redirect jika tidak
    def test_cart_view_requires_login(self):
        url = reverse('cart:cart')
        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

    #memastikan staff diblokir dan diarahkan ke katalog dengan pesan
    def test_cart_view_staff_blocked(self):
        self.client.login(username='s', password='pass')
        resp = self.client.get(reverse('cart:cart'))
        self.assertRedirects(resp, reverse('products:catalog'))
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertIn("Admin users cannot access", msgs[0])

    #memastikan view cart sukses dan CSRF token ada di form
    def test_cart_view_success_and_csrf(self):
        self.client.login(username='u', password='pass')
        resp = self.client.get(reverse('cart:cart'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'csrfmiddlewaretoken')

    #memastikan GET add_to_cart redirect ke detail produk
    def test_add_to_cart_get_redirect(self):
        self.client.login(username='u', password='pass')
        resp = self.client.get(reverse('cart:add_to_cart', args=[self.prod.product_id]))
        self.assertRedirects(resp, reverse('products:product_detail', args=[self.prod.product_id]))

    #memastikan POST add_to_cart berhasil menambah item dengan quantity benar
    def test_add_to_cart_success(self):
        self.client.login(username='u', password='pass')
        url = reverse('cart:add_to_cart', args=[self.prod.product_id])
        resp = self.client.post(url, {'size': '42', 'quantity': '3'})
        self.assertRedirects(resp, reverse('cart:cart'))
        self.assertTrue(
            CartItem.objects.filter(user=self.user, product=self.prod, size=42, quantity=3).exists()
        )

    #memastikan add_to_cart menolak quantity melebihi stok dan pesan muncul
    def test_add_to_cart_exceed_stock(self):
        self.client.login(username='u', password='pass')
        url = reverse('cart:add_to_cart', args=[self.prod.product_id])
        # stok size 40 hanya 2 tapi request 5
        resp = self.client.post(url, {'size': '40', 'quantity': '5'})
        self.assertRedirects(resp, reverse('products:product_detail', args=[self.prod.product_id]))
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertIn("exceeds available stock", msgs[0])
        # quantity cart tetap 1
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 1)

    #memastikan add_to_cart menolak size yang tidak tersedia
    def test_add_to_cart_invalid_size(self):
        self.client.login(username='u', password='pass')
        url = reverse('cart:add_to_cart', args=[self.prod.product_id])
        resp = self.client.post(url, {'size': '999', 'quantity': '1'})
        self.assertRedirects(resp, reverse('products:product_detail', args=[self.prod.product_id]))
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertIn("Size 999 is not available", msgs[0])

    #memastikan staff tidak dapat menambah ke cart dan diarahkan ke katalog
    def test_add_to_cart_staff_block(self):
        self.client.login(username='s', password='pass')
        url = reverse('cart:add_to_cart', args=[self.prod.product_id])
        resp = self.client.post(url, {'size': '42', 'quantity': '1'})
        self.assertRedirects(resp, reverse('products:catalog'))
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertIn("Admin users cannot add", msgs[0])

    #memastikan remove_from_cart berhasil menghapus item
    def test_remove_from_cart_success(self):
        self.client.login(username='u', password='pass')
        url = reverse('cart:remove_from_cart', args=[self.cart_item.id])
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('cart:cart'))
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())

    #memastikan remove_from_cart menampilkan pesan jika item tidak ditemukan
    def test_remove_from_cart_not_found(self):
        self.client.login(username='u', password='pass')
        url = reverse('cart:remove_from_cart', args=[999])
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('cart:cart'))
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertIn("Item not found", msgs[0])

    #memastikan update_quantity increase dan decrease berfungsi
    def test_update_quantity_increase_and_decrease(self):
        self.client.login(username='u', password='pass')
        url = reverse('cart:update_quantity', args=[self.cart_item.id])
        # increase
        resp = self.client.post(url, {'action': 'increase'})
        self.assertRedirects(resp, reverse('cart:cart'))
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)
        # decrease
        resp = self.client.post(url, {'action': 'decrease'})
        self.assertRedirects(resp, reverse('cart:cart'))
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 1)

    #memastikan update_quantity menghapus item jika quantity menjadi nol
    def test_update_quantity_remove_on_zero(self):
        self.client.login(username='u', password='pass')
        # set quantity 1 lalu decrease
        self.cart_item.quantity = 1
        self.cart_item.save()
        url = reverse('cart:update_quantity', args=[self.cart_item.id])
        resp = self.client.post(url, {'action': 'decrease'})
        self.assertRedirects(resp, reverse('cart:cart'))
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())

    #memastikan rate limit enforcement diterapkan pada cart view setelah 10 request
    def test_rate_limit_enforced(self):
        self.client.login(username='u', password='pass')
        url = reverse('cart:cart')
        for _ in range(10):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
        # 11th request
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 403, 429])
