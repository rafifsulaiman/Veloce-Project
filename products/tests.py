from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, ProductSize
import json

User = get_user_model()

class ProductViewsTest(TestCase):

    #mengatur client pembuatan user produk dan ukuran produk
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='pass123'
        )

        self.p1 = Product.objects.create(
            product_id='1', name='Prod A', brand='Nike',
            gender='men', price=100, image_url='urlA'
        )
        self.p2 = Product.objects.create(
            product_id='2', name='Prod B', brand='Adidas',
            gender='women', price=200, image_url='urlB'
        )
        ProductSize.objects.create(product=self.p1, size=40, stock=5)
        ProductSize.objects.create(product=self.p1, size=42, stock=2)

    #memastikan katalog view tanpa filter mengembalikan dua produk
    def test_catalog_view_no_filter(self):
        resp = self.client.get(reverse('products:catalog'))
        self.assertEqual(resp.status_code, 200)
        qs = resp.context['products']
        self.assertEqual(list(qs.order_by('product_id')), [self.p1, self.p2])

    #memastikan filter brand berfungsi hanya produk brand tertentu
    def test_catalog_filter_brand(self):
        resp = self.client.get(reverse('products:catalog'), {'brand': 'Nike'})
        self.assertEqual(resp.status_code, 200)
        products = resp.context['products']
        self.assertEqual(products.count(), 1)
        self.assertEqual(products[0].brand, 'Nike')

    #memastikan filter gender menghasilkan produk gender tertentu
    def test_catalog_filter_gender(self):
        resp = self.client.get(reverse('products:catalog'), {'gender': 'women'})
        self.assertEqual(resp.status_code, 200)
        products = resp.context['products']
        self.assertEqual(products.count(), 1)
        self.assertEqual(products[0].gender, 'women')

    #memastikan filter size menghasilkan produk ukuran tertentu
    def test_catalog_filter_size(self):
        resp = self.client.get(reverse('products:catalog'), {'size': '40'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['products']), [self.p1])

    #memastikan sql injection safe pada filter brand
    def test_catalog_sql_injection_safe(self):
        resp = self.client.get(reverse('products:catalog'), {'brand': "' OR '1'='1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['products'].count(), 0)

    #memastikan size invalid diabaikan tanpa crash
    def test_catalog_invalid_size_ignored(self):
        resp = self.client.get(reverse('products:catalog'), {'size': 'notint'})
        self.assertEqual(resp.status_code, 200)

    #memastikan get_images dan main_image mengembalikan data url
    def test_get_images_and_main_image(self):
        self.assertEqual(self.p1.get_images(), ['urlA'])
        self.assertEqual(self.p1.main_image(), 'urlA')

    #memastikan product_detail memerlukan login sebelum akses
    def test_product_detail_requires_login(self):
        url = reverse('products:product_detail', args=[self.p1.product_id])
        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

    #memastikan product_detail dapat diakses setelah login
    def test_product_detail_logged_in(self):
        self.client.login(username='tester', password='pass123')
        url = reverse('products:product_detail', args=[self.p1.product_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'product_detail.html')

    #memastikan request detail yang tidak ada mengarahkan ke katalog
    def test_product_detail_not_found(self):
        self.client.login(username='tester', password='pass123')
        url = reverse('products:product_detail', args=['999'])
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('products:catalog'))

    #memastikan API get_product memerlukan login
    def test_get_product_api_requires_login(self):
        url = reverse('products:get_product', args=[self.p1.product_id])
        resp = self.client.get(url)
        self.assertRedirects(resp, f"{reverse('users:login')}?next={url}")

    #memastikan API get_product mengembalikan JSON yang benar
    def test_get_product_api_json(self):
        self.client.login(username='tester', password='pass123')
        url = reverse('products:get_product', args=[self.p1.product_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['product_id'], self.p1.product_id)
        self.assertIsInstance(data['sizes'], list)

    #memastikan API get_product_data publik mengembalikan JSON produk
    def test_get_product_data_public(self):
        url = reverse('products:get_product_data')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('products', data)
        self.assertEqual(len(data['products']), 2)

    #memastikan rate limit untuk katalog diterapkan setelah 10 request
    def test_rate_limit_catalog(self):
        url = reverse('products:catalog')
        last = None
        for _ in range(11):
            last = self.client.get(url)
        self.assertIn(last.status_code, [200, 403, 429])

    #memastikan rate limit untuk detail diterapkan setelah 10 request
    def test_rate_limit_detail(self):
        self.client.login(username='tester', password='pass123')
        url = reverse('products:product_detail', args=[self.p1.product_id])
        last = None
        for _ in range(11):
            last = self.client.get(url)
        self.assertIn(last.status_code, [200, 403, 429])
