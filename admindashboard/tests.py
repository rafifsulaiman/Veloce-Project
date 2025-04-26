from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, ProductSize
from transaction.models import Transaction, AuditLog, OrderItem
from decimal import Decimal

User = get_user_model()

class AdminDashboardViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # normal user
        self.user = User.objects.create_user(
            username='user', email='user@example.com', password='pass'
        )
        # staff user
        self.staff = User.objects.create_user(
            username='staff', email='staff@example.com',
            password='pass', is_staff=True
        )
        # superuser
        self.super = User.objects.create_superuser(
            username='super', email='super@example.com', password='pass'
        )

        # Product and sizes
        self.prod = Product.objects.create(
            product_id='P1',
            name='Test Product',
            brand='Nike',
            gender='men',
            price=50,
            image_url='["img1","img2"]'
        )
        ProductSize.objects.create(product=self.prod, size=38, stock=3)
        ProductSize.objects.create(product=self.prod, size=40, stock=2)

        # Transaction with all required fields
        self.tx = Transaction.objects.create(
            transaction_id='T1',
            user=self.user,
            status='pending',
            transaction_amount=Decimal('100.00'),
            delivery_price=Decimal('25000.00'),
            shipping_status='processing',
            shipping_address='123 Test St',
            shipping_city='CityX',
            shipping_postal_code='12345',
            payment_method='velocepay'
        )

        # OrderItem with required fields
        OrderItem.objects.create(
            transaction=self.tx,
            product=self.prod,
            product_name=self.prod.name,
            product_price=Decimal(self.prod.price),
            quantity=1,
            size=38
        )

        # AuditLog
        self.log = AuditLog.objects.create(
            admin_user=self.super,
            transaction=self.tx,
            action='view',
            details='initial log',
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )

    def test_admin_page_requires_staff(self):
        url = reverse('admindashboard:admin_page')
        # anonymous -> login
        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

        # normal user -> redirect to catalog
        self.client.login(username='user', password='pass')
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('products:catalog'))

        # staff -> can view
        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertIn('total_stock', ctx)
        self.assertIn('brands_count', ctx)
        self.assertIn('sizes_count', ctx)

    def test_admin_page_search_and_pagination(self):
        self.client.login(username='super', password='pass')
        url = reverse('admindashboard:admin_page')
        resp = self.client.get(url, {'search': "' OR '1'='1"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(url, {'page': 'notanint'})
        self.assertEqual(resp.status_code, 200)

    def test_add_product_rbac_and_form(self):
        url = reverse('admindashboard:add_product')
        self.client.login(username='user', password='pass')
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('products:catalog'))

        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 200)

        data = {
            'brand': 'Adidas',
            'name': 'NewProd',
            'product_id': 'P2',
            'price': 123,
            'image_url': '["i"]',
            'sizes': ['36', '37']
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        # self.assertTrue(Product.objects.filter(product_id='P2').exists())

    def test_edit_product_login_required(self):
        url = reverse('admindashboard:edit_product', args=['P1'])
        payload = {'name': 'Edited'}
        resp = self.client.post(url, payload, content_type='application/json')
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

        self.client.login(username='staff', password='pass')
        resp = self.client.post(url, payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.name, 'Edited')

    def test_delete_product_rbac(self):
        url = reverse('admindashboard:delete_product', args=['P1'])
        self.client.login(username='user', password='pass')
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('products:catalog'))

        self.client.login(username='staff', password='pass')
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('admindashboard:admin_page'))
        self.assertFalse(Product.objects.filter(product_id='P1').exists())

    def test_admin_transaction_list_rbac_and_filter(self):
        url = reverse('admindashboard:admin_transaction_list')
        self.client.login(username='user', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url, {
            'status': 'pending',
            'start_date': 'bad',
            'end_date': 'bad',
            'query': "' OR '1'"
        })
        self.assertEqual(resp.status_code, 200)

    def test_admin_transaction_detail_and_notfound(self):
        url = reverse('admindashboard:admin_transaction_detail', args=['T1'])
        self.client.login(username='super', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        url2 = reverse('admindashboard:admin_transaction_detail', args=['X'])
        resp = self.client.get(url2)
        self.assertRedirects(resp, reverse('admindashboard:admin_transaction_list'))

    def test_update_transaction_status_permissions(self):
        url = reverse('admindashboard:admin_update_status', args=['T1'])
        # normal user -> admin login
        self.client.login(username='user', password='pass')
        resp = self.client.post(url)
        expected = f"{reverse('admin:login')}?next={url}"
        self.assertRedirects(resp, expected)

        # staff GET -> 405
        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

        # staff POST -> success
        resp = self.client.post(url, {
            'payment_status': 'paid',
            'shipping_status': 'shipped'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'success')

    def test_cancel_transaction_permissions(self):
        url = reverse('admindashboard:admin_cancel_transaction', args=['T1'])
        # normal user -> admin login
        self.client.login(username='user', password='pass')
        resp = self.client.post(url)
        expected = f"{reverse('admin:login')}?next={url}"
        self.assertRedirects(resp, expected)

        # staff GET -> 405
        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

        # staff POST -> success
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'success')

    def test_audit_logs_rbac_and_filter(self):
        url = reverse('admindashboard:admin_audit_logs')
        # normal user -> admin login
        self.client.login(username='user', password='pass')
        resp = self.client.get(url)
        expected = f"{reverse('admin:login')}?next={url}"
        self.assertRedirects(resp, expected)

        # superuser filter -> 200
        self.client.login(username='super', password='pass')
        resp = self.client.get(url, {
            'action': 'view',
            'start_date': self.log.timestamp.strftime('%Y-%m-%d'),
            'end_date': self.log.timestamp.strftime('%Y-%m-%d'),
            'admin': self.super.username
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('page_obj', resp.context)
