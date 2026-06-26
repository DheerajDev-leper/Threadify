from django.db import models
from store.models import Product, ProductVariant
from accounts.models import Account

# Create your models here.
class Cart(models.Model):
    date_added = models.DateTimeField(auto_now_add=True)
    cart_id = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        price = self.variant.effective_price if self.variant else self.product.price
        return price * self.quantity

    def __unicode__(self):
        return self.product