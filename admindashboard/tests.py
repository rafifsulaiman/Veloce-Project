from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from products.models import Product, Size
from transaction.models import Transaction, AuditLog, OrderItem
from datetime import datetime, timedelta
import json

User = get_user_model()

class AdminDashboardViewsTest(TestCase):
    def setUp(self):
        # Client & users
        self.client = Client()
        # non-staff user
        self.user = User.objects.create_user('user', 'u@e.com', 'pass')
        # staff but no perms
        self.staff = User.objects.create_user('staff', 's@e.com', 'pass', is_staff=True)
        # superuser (staff + all perms)
        self.super = User.objects.create_superuser('super', 'su@e.com', 'pass')

        # sample product
        self.prod = Product.objects.create(
            product_id='P1', name='Test', brand='X', gender='U',
            price=50, image_url='u', size='[]'
        )

        # sizes for stock count
        Size.objects.create(product=self.prod, size=38, stock=3)
        Size.objects.create(product=self.prod, size=40, stock=2)

        # sample transaction
        self.tx = Transaction.objects.create(
            transaction_id='T1',
            user=self.user,
            shipping_city='CityX',
            status='pending',
            shipping_status='pending',
            date_created=datetime.now()
        )
        # an order item
        OrderItem.objects.create(transaction=self.tx, product=self.prod, quantity=1, price=50)

        # one audit log
        self.log = AuditLog.objects.create(
            admin_user=self.super,
            transaction=self.tx,
            action='view',
            details='init',
            ip_address='127.0.0.1',
            user_agent='test'
        )

    def test_admin_page_requires_staff(self):
        url = reverse('admindashboard:admin_page')
        # anonymous
        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")
        # normal user
        self.client.login(username='user', password='pass')
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('products:catalog'))
        # staff user
        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # context checks
        self.assertIn('total_stock', resp.context)
        self.assertIn('brands_count', resp.context)
        self.assertIn('sizes_count', resp.context)

    def test_admin_page_search_and_pagination(self):
        self.client.login(username='super', password='pass')
        url = reverse('admindashboard:admin_page')
        # search injection-safe
        resp = self.client.get(url, {'search': "' OR '1'='1"})
        self.assertEqual(resp.status_code, 200)
        # invalid page number -> defaults to page 1
        resp = self.client.get(url, {'page': 'notanint'})
        self.assertEqual(resp.status_code, 200)

    def test_add_product_rbac_and_form(self):
        url = reverse('admindashboard:add_product')
        # non-staff
        self.client.login(username='user', password='pass')
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('products:catalog'))
        # staff GET
        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # staff POST invalid -> form invalid
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 200)
        # staff POST valid
        data = {
            'brand':'Y','name':'New','product_id':'P2',
            'price':10,'image_url':'u','sizes':['36','37']
        }
        with open(__file__, 'rb') as fake:  # dummy file for FILES
            resp = self.client.post(url, data=data)
        # should redirect to catalog
        self.assertRedirects(resp, reverse('products:catalog'))
        self.assertTrue(Product.objects.filter(product_id='P2').exists())

    def test_edit_product_login_required(self):
        url = reverse('admindashboard:edit_product', args=['P1'])
        # anonymous
        resp = self.client.post(url, json.dumps({'name':'Z'}),
                                content_type='application/json')
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")
        # staff can edit
        self.client.login(username='staff', password='pass')
        payload = {'name':'Z','price':99,'sizes':[38],'image_url':'new'}
        resp = self.client.post(url, json.dumps(payload),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('message', data)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.name, 'Z')

    def test_delete_product_rbac(self):
        url = reverse('admindashboard:delete_product', args=['P1'])
        # non-staff
        self.client.login(username='user', password='pass')
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('products:catalog'))
        # staff
        self.client.login(username='staff', password='pass')
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('admindashboard:admin_page'))
        self.assertFalse(Product.objects.filter(product_id='P1').exists())

    def test_admin_transaction_list_rbac_and_filter(self):
        url = reverse('admindashboard:admin_transaction_list')
        # non-staff
        self.client.login(username='user', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)  # redirect to /admin/login/
        # staff without perm still allowed by staff_member_required
        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # filter status, date, query
        resp = self.client.get(url, {
            'status':'pending',
            'start_date':'badformat','end_date':'x',
            'query':"' OR '1'"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('page_obj', resp.context)

    def test_admin_transaction_detail_and_notfound(self):
        url = reverse('admindashboard:admin_transaction_detail', args=['T1'])
        # staff
        self.client.login(username='super', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'transaction_detail.html')
        # not exists
        url2 = reverse('admindashboard:admin_transaction_detail', args=['NOPE'])
        resp = self.client.get(url2)
        self.assertRedirects(resp, reverse('admindashboard:admin_transaction_list'))

    def test_update_transaction_status_permissions(self):
        url = reverse('admindashboard:admin_update_status', args=['T1'])
        # GET not allowed
        self.client.login(username='super', password='pass')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)
        # staff without perm -> 403
        self.client.login(username='staff', password='pass')
        resp = self.client.post(url, {'payment_status':'paid'})
        self.assertEqual(resp.status_code, 403)
        # staff with specific perm
        perm = Permission.objects.get(codename='change_transaction')
        self.staff.user_permissions.add(perm)
        resp = self.client.post(url, {
            'payment_status':'paid',
            'shipping_status':'shipped'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')

    def test_cancel_transaction_permissions(self):
        url = reverse('admindashboard:admin_cancel_transaction', args=['T1'])
        self.client.login(username='staff', password='pass')
        # without perm -> 403
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)
        # grant delete_transaction perm
        perm = Permission.objects.get(codename='delete_transaction')
        self.staff.user_permissions.add(perm)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')

    def test_audit_logs_rbac_and_filter(self):
        url = reverse('admindashboard:admin_audit_logs')
        # non-staff
        self.client.login(username='user', password='pass')
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('admindashboard:admin_transaction_list'))
        # staff without view perm
        self.client.login(username='staff', password='pass')
        resp = self.client.get(url)
        # still accessible but should contain page_obj
        self.assertEqual(resp.status_code, 200)
        # filter by action, date, admin
        self.client.login(username='super', password='pass')
        resp = self.client.get(url, {
            'action':'view',
            'start_date':self.log.timestamp.strftime('%Y-%m-%d'),
            'end_date':self.log.timestamp.strftime('%Y-%m-%d'),
            'admin':self.super.username
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('page_obj', resp.context)
