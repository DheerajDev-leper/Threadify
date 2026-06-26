from django.contrib import admin
from .models import Product, ProductVariant, ReviewRating, ProductGallery
import admin_thumbnails

# Register your models here.

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'is_available', 'category', 'created_date', 'modified_date')
    prepopulated_fields = {'slug': ('product_name',)}
    list_editable = ('price', 'stock', 'is_available')
    inlines = [ProductGalleryInline]

class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'sku', 'price', 'stock', 'is_active', 'created_date')
    list_editable = ('stock', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('product__product_name', 'color', 'size', 'sku')

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)