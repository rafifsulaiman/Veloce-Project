import csv
import json
from django.core.management.base import BaseCommand
from main.models import Product

class Command(BaseCommand):
    help = 'Import products from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        total_imported = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Check if the product already exists
                    product, created = Product.objects.get_or_create(
                        product_id=row['product_id'],
                        defaults={
                            'brand': row['brand'],
                            'name': row['name'],
                            'price': int(row['price']),
                            'size': int(row['size']),
                            'image_url': row['image_url']
                        }
                    )
                    
                    if created:
                        total_imported += 1
                        self.stdout.write(f"Imported: {product.brand} - {product.name}")
                    else:
                        self.stdout.write(f"Already exists: {product.brand} - {product.name}")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error importing {row.get('name', 'unknown product')}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {total_imported} products")) 