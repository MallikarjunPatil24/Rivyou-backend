from django.db import models


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    product_description = models.TextField()
    category = models.CharField(
        max_length=100,
        choices=[
            ('Smartphones', 'Smartphones'),
            ('Chargers', 'Chargers'),
            ('Back Covers', 'Back Covers'),
        ]
    )
    tags = models.JSONField(default=list, help_text='List of tag strings e.g. ["5g", "camera"]')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['category'], name='idx_product_category'),
            models.Index(fields=['tags'], name='idx_product_tags'),
        ]

    def __str__(self):
        return f"{self.product_name} ({self.category})"
