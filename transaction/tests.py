from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from transaction.models import Transaction, OrderItem
from cart.models import CartItem
from products.models import Product, ProductSize
from users.models import Address

User = get_user_model()

class TransactionViewsTests(TestCase):

    #mengatur client dan objek awal untuk pengujian transaksi
    def setUp(self):
        self.client = Client()
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password'
        )
        # Create admin staff user
        self.staff_user = User.objects.create_user(
            username='adminuser',
            email='adminuser@example.com',
            password='password',
            is_staff=True
        )
        # Create product and size
        self.product = Product.objects.create(name="Test Product", price=100000, brand='Nike', product_id='TP001', gender='unisex', image_url='')
        self.product_size = ProductSize.objects.create(product=self.product, size=42, stock=10)
        # Create address with required fields
        self.address = Address.objects.create(
            user=self.user,
            name='Test User',
            phone_number='081234567890',
            street_address='123 Test Street',
            village='Test Village',
            district='Test District',
            city='Test City',
            province='Test Province',
            postal_code='12345'
        )

    #memastikan view checkout memerlukan login dan mengarahkan ke halaman login
    def test_checkout_view_requires_login(self):
        response = self.client.get(reverse('transaction:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    #memastikan admin tidak dapat checkout dan pesan kesalahan ditampilkan
    def test_checkout_view_redirects_admin(self):
        self.client.login(username='adminuser', password='password')
        response = self.client.get(reverse('transaction:checkout'))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Admin users cannot checkout.", [m.message for m in messages])

    #memastikan pengguna dengan keranjang kosong diarahkan dan pesan your cart is empty ditampilkan
    def test_checkout_view_empty_cart_redirect(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:checkout'))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Your cart is empty.", [m.message for m in messages])

    #memastikan view checkout menampilkan form saat keranjang tidak kosong
    def test_checkout_view_displays_form(self):
        CartItem.objects.create(user=self.user, product=self.product, size=42, quantity=1)
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    #memastikan checkout confirm memeriksa keberadaan data di session dan meminta pengguna melengkapi form
    def test_checkout_confirm_requires_session_data(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:checkout_confirm'))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Please complete the checkout form.", [m.message for m in messages])

    #memastikan checkout confirm menampilkan pesan selected address not found saat alamat tidak valid
    def test_checkout_confirm_invalid_address(self):
        CartItem.objects.create(user=self.user, product=self.product, size=42, quantity=1)
        session = self.client.session
        session['checkout_data'] = {'address_id': 9999, 'payment_method': 'velocepay'}
        session.save()
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:checkout_confirm'))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Selected address not found.", [m.message for m in messages])

    #memastikan checkout confirm berhasil saat data session valid dan status code 200
    def test_checkout_confirm_success(self):
        CartItem.objects.create(user=self.user, product=self.product, size=42, quantity=1)
        session = self.client.session
        session['checkout_data'] = {'address_id': self.address.id, 'payment_method': 'velocepay'}
        session.save()
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:checkout_confirm'))
        self.assertEqual(response.status_code, 200)

    #memastikan post ke checkout confirm membuat transaksi baru saat data valid
    def test_checkout_confirm_post_creates_transaction(self):
        CartItem.objects.create(user=self.user, product=self.product, size=42, quantity=1)
        session = self.client.session
        session['checkout_data'] = {'address_id': self.address.id, 'payment_method': 'velocepay'}
        session.save()
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('transaction:checkout_confirm'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaction.objects.filter(user=self.user).exists())

    #memastikan process payment memerlukan login dan mengarahkan ke login jika tidak
    def test_process_payment_requires_login(self):
        txn = Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-TESTPAY",
            status='pending',
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        response = self.client.get(reverse('transaction:process_payment', args=[txn.transaction_id]))
        self.assertEqual(response.status_code, 302)

    #memastikan status transaksi diubah ke processing saat pembayaran berhasil
    def test_process_payment_success(self):
        txn = Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-TESTPAY",
            status='pending',
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        OrderItem.objects.create(
            transaction=txn,
            product=self.product,
            product_name=self.product.name,
            product_price=self.product.price,
            quantity=1,
            size=42
        )
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:process_payment', args=[txn.transaction_id]))
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'processing')

    #memastikan halaman success dapat diakses untuk transaksi yang ada
    def test_transaction_success_page(self):
        txn = Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-SUCCESS",
            status='pending',
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:success', args=[txn.transaction_id]))
        self.assertEqual(response.status_code, 200)

    #memastikan order history menampilkan daftar transaksi pengguna
    def test_order_history_shows_transactions(self):
        Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-HISTORY",
            status='pending',
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:order_history'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('transactions', response.context)

    #memastikan order detail view menampilkan detail transaksi yang dipilih
    def test_order_detail_view(self):
        txn = Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-DETAIL",
            status='pending',
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:order_detail', args=[txn.transaction_id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('transaction', response.context)

    #memastikan cancel order memerlukan admin dan mengarahkan jika bukan admin
    def test_cancel_order_requires_admin(self):
        txn = Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-CANCEL",
            status='pending',
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:cancel_order', args=[txn.transaction_id]))
        self.assertEqual(response.status_code, 302)

    #memastikan admin dapat membatalkan pesanan dan status berubah menjadi cancelled
    def test_cancel_order_success_as_admin(self):
        txn = Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-CANCELADMIN",
            status='pending',
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        OrderItem.objects.create(
            transaction=txn,
            product=self.product,
            product_name=self.product.name,
            product_price=self.product.price,
            quantity=1,
            size=42
        )
        self.client.login(username='adminuser', password='password')
        response = self.client.get(reverse('transaction:cancel_order', args=[txn.transaction_id]))
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'cancelled')

    #memastikan checkout gagal dan pesan kesalahan saat stok tidak mencukupi
    def test_checkout_confirm_post_fails_when_stock_insufficient(self):
        # Setup cart item lebih banyak dari stock
        CartItem.objects.create(user=self.user, product=self.product, size=42, quantity=20)  # Stock hanya 10
        session = self.client.session
        session['checkout_data'] = {'address_id': self.address.id, 'payment_method': 'velocepay'}
        session.save()
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('transaction:checkout_confirm'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("There are no valid items in your cart" in m.message for m in messages))
        self.assertEqual(response.status_code, 302)
        # Pastikan tidak ada transaksi tercipta
        self.assertFalse(Transaction.objects.filter(user=self.user).exists())

    #memastikan process payment menolak transaksi yang sudah processing dengan pesan kesalahan
    def test_process_payment_already_processing_redirects(self):
        # Setup transaction sudah processing
        txn = Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-ALREADYPROC",
            status='processing',  # Sudah diproses
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('transaction:process_payment', args=[txn.transaction_id]))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already been processed" in m.message for m in messages))
        self.assertEqual(response.status_code, 302)

    #memastikan cancel order menolak transaksi yang sudah cancelled dengan pesan kesalahan
    def test_cancel_order_already_cancelled(self):
        # Setup transaction yang sudah cancelled
        txn = Transaction.objects.create(
            user=self.user,
            transaction_id="TRX-CANCELLED",
            status='cancelled',
            transaction_amount=100000,
            delivery_price=25000,
            shipping_address=self.address.get_complete_address(),
            shipping_city=self.address.city,
            shipping_postal_code=self.address.postal_code
        )
        self.client.login(username='adminuser', password='password')
        response = self.client.get(reverse('transaction:cancel_order', args=[txn.transaction_id]))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already been cancelled" in m.message for m in messages) or 
                      any("already cancelled" in m.message for m in messages))
        self.assertEqual(response.status_code, 302)

    #memastikan keranjang dikosongkan setelah checkout berhasil
    def test_cart_is_cleared_after_successful_checkout(self):
        CartItem.objects.create(user=self.user, product=self.product, size=42, quantity=1)
        session = self.client.session
        session['checkout_data'] = {'address_id': self.address.id, 'payment_method': 'velocepay'}
        session.save()
        self.client.login(username='testuser', password='password')
        self.client.post(reverse('transaction:checkout_confirm'))
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    #memastikan data checkout di session dihapus setelah checkout selesai
    def test_checkout_data_session_cleared_after_checkout(self):
        CartItem.objects.create(user=self.user, product=self.product, size=42, quantity=1)
        session = self.client.session
        session['checkout_data'] = {'address_id': self.address.id, 'payment_method': 'velocepay'}
        session.save()
        self.client.login(username='testuser', password='password')
        self.client.post(reverse('transaction:checkout_confirm'))
        # Reload session
        session = self.client.session
        self.assertNotIn('checkout_data', session)

    #memastikan payment url dibuat dan menyertakan transaction id
    def test_payment_url_is_generated_and_saved(self):
        CartItem.objects.create(user=self.user, product=self.product, size=42, quantity=1)
        session = self.client.session
        session['checkout_data'] = {'address_id': self.address.id, 'payment_method': 'velocepay'}
        session.save()
        self.client.login(username='testuser', password='password')
        self.client.post(reverse('transaction:checkout_confirm'))
        txn = Transaction.objects.filter(user=self.user).first()
        self.assertIsNotNone(txn.payment_url)
        self.assertIn(txn.transaction_id, txn.payment_url)
