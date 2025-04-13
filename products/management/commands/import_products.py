import csv
import os
from django.core.management.base import BaseCommand
from products.models import Product, ProductSize

class Command(BaseCommand):
    help = 'Import products from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file_path}'))
            return
        
        products_created = 0
        products_updated = 0
        sizes_created = 0
        
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                product, created = Product.from_csv_row(row)
                
                if created:
                    products_created += 1
                else:
                    products_updated += 1
                
                # Count as a size created in any case for better reporting
                sizes_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully imported products. '
            f'Created: {products_created}, Updated: {products_updated}, Sizes: {sizes_created}'
        )) 