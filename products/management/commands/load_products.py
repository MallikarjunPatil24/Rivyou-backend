import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Product

class Command(BaseCommand):
    help = 'Load products data from products_data.csv in the BASE_DIR'

    def handle(self, *args, **options):
        # Try both singular and plural forms of the filename
        possible_filenames = ['product_data.csv', 'products_data.csv']
        csv_file_path = None
        
        for filename in possible_filenames:
            path_to_check = os.path.join(settings.BASE_DIR, filename)
            if os.path.exists(path_to_check):
                csv_file_path = path_to_check
                break

        if not csv_file_path:
            self.stdout.write(self.style.ERROR(
                f'CSV file not found. Checked: {", ".join(possible_filenames)} under {settings.BASE_DIR}'
            ))
            return

        self.stdout.write(self.style.NOTICE(f'Reading products from {csv_file_path}...'))

        # Auto-detect encoding
        encodings = ['utf-8-sig', 'cp1252', 'utf-16', 'utf-8', 'latin-1']
        detected_encoding = 'utf-8'
        for enc in encodings:
            try:
                with open(csv_file_path, mode='r', encoding=enc) as f:
                    f.read(4096)  # Test reading a block of characters
                detected_encoding = enc
                break
            except UnicodeDecodeError:
                continue

        self.stdout.write(self.style.NOTICE(f"Detected encoding: {detected_encoding}"))

        # Count total lines for progress report
        try:
            with open(csv_file_path, mode='r', encoding=detected_encoding) as f:
                total_products = sum(1 for _ in csv.DictReader(f))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to read total count from CSV: {e}'))
            return

        loaded_count = 0
        success_count = 0

        with open(csv_file_path, mode='r', encoding=detected_encoding) as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    product_id = int(row['id'])
                    name = row['product_name'].strip()
                    description = row['product_description'].strip()
                    category = row['category'].strip()
                    
                    # Parse tags (comma-separated to list of strings)
                    tags_str = row.get('tags', '')
                    tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()]

                    # get_or_create to avoid duplicates if run twice
                    product, created = Product.objects.get_or_create(
                        id=product_id,
                        defaults={
                            'product_name': name,
                            'product_description': description,
                            'category': category,
                            'tags': tags_list
                        }
                    )
                    
                    # Update fields if product exists but properties are different
                    if not created:
                        updated = False
                        if product.product_name != name:
                            product.product_name = name
                            updated = True
                        if product.product_description != description:
                            product.product_description = description
                            updated = True
                        if product.category != category:
                            product.category = category
                            updated = True
                        if product.tags != tags_list:
                            product.tags = tags_list
                            updated = True
                        if updated:
                            product.save()

                    success_count += 1
                    loaded_count += 1

                    if loaded_count % 100 == 0:
                        self.stdout.write(f'Loaded {loaded_count}/{total_products} products...')

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error loading row {row.get('id', 'unknown')}: {str(e)}")
                    )
                    loaded_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {success_count} products')
        )
