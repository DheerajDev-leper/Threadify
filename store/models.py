from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from category.models import Category
from django.conf import settings
from accounts.models import Account


class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    Image = models.ImageField(upload_to='photos/products')
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    shop = models.ForeignKey(
        'Shop',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name

    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

    def has_variants(self):
        return self.variants.exists()

    def available_colors(self):
        return (
            self.variants.filter(is_active=True)
            .exclude(color='')
            .values_list('color', flat=True)
            .distinct()
            .order_by('color')
        )

    def available_sizes(self):
        return (
            self.variants.filter(is_active=True)
            .exclude(size='')
            .values_list('size', flat=True)
            .distinct()
            .order_by('size')
        )


class ProductVariant(models.Model):
    """
    One purchasable colour/size combination for a product (e.g. "Red / XL"),
    with its own stock count and optional price override.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=64, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['color', 'size']
        unique_together = ('product', 'color', 'size')

    def __str__(self):
        return f'{self.product.product_name} — {self.display_label}'

    @property
    def display_label(self):
        parts = [p for p in (self.color, self.size) if p]
        return ' / '.join(parts) if parts else 'Default'

    @property
    def effective_price(self):
        return self.price if self.price is not None else self.product.price

    @property
    def in_stock(self):
        return self.is_active and self.stock > 0


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    # ── NEW: tag this image to a specific colour variant ──────────────────
    # Leave blank → image appears for every colour (useful for lifestyle/
    # packaging shots that aren't colour-specific).
    # Set to e.g. "Blue" → image only shows when Blue is selected.
    color = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Leave blank to show for all colours, or enter a colour '
                  'name to show only when that colour is selected.',
    )

    def __str__(self):
        label = f' [{self.color}]' if self.color else ''
        return f'{self.product.product_name}{label}'

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'


class Shop(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shop',
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='shop_logos/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name