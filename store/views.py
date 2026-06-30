import json
from collections import defaultdict

from django.contrib import messages
from django.shortcuts import redirect, render
from django.db.models import Min, Q

from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category

from orders.models import OrderProduct

from .forms import ReviewForm
from .models import Product, ProductGallery, ReviewRating, ProductVariant, Shop
from django.core.paginator import Paginator


def store(request, category_slug=None):
    categories = None
    products = Product.objects.filter(is_available=True)

    # ── Category filter ──────────────────────────────
    if category_slug:
        categories = Category.objects.get(slug=category_slug)
        products = products.filter(category=categories)

    # ── Size filter ──────────────────────────────────
    selected_sizes = request.GET.getlist('size')
    if selected_sizes:
        products = products.filter(
            variants__size__in=selected_sizes,
            variants__is_active=True
        ).distinct()

    # ── Color filter ─────────────────────────────────
    selected_colors = request.GET.getlist('color')
    if selected_colors:
        products = products.filter(
            variants__color__in=selected_colors,
            variants__is_active=True
        ).distinct()

    # ── Price range filter (via variant prices) ──────
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        products = products.filter(
            variants__price__gte=min_price,
            variants__is_active=True
        ).distinct()
    if max_price:
        products = products.filter(
            variants__price__lte=max_price,
            variants__is_active=True
        ).distinct()

    # ── Annotate lowest variant price ────────────────
    products = products.annotate(
        min_variant_price=Min('variants__price')
    )

    # ── Count before pagination ──────────────────────
    products_count = products.count()

    # ── Available filter options scoped to current product set ──
    available_sizes = ProductVariant.objects.filter(
        is_active=True,
        product__in=products            # ← scoped to category/filters
    ).exclude(size='').values_list('size', flat=True).distinct().order_by('size')

    available_colors = ProductVariant.objects.filter(
        is_active=True,
        product__in=products            # ← scoped to category/filters
    ).exclude(color='').values_list('color', flat=True).distinct().order_by('color')

    # ── Pagination ───────────────────────────────────
    products = products.order_by('id')
    per_page = 3 if category_slug else 9
    paginator = Paginator(products, per_page)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    context = {
        'products':         paged_products,
        'products_count':   products_count,
        'available_sizes':  available_sizes,
        'available_colors': available_colors,
        'selected_sizes':   selected_sizes,
        'selected_colors':  selected_colors,
        'min_price':        min_price,
        'max_price':        max_price,
    }
    return render(request, 'store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(
            category__slug=category_slug,
            slug=product_slug
        )
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request),
            product=single_product
        ).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(
                user=request.user,
                product_id=single_product.id
            ).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    reviews         = ReviewRating.objects.filter(product_id=single_product.id, status=True)
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    # ── Variant picker data ───────────────────────────
    active_variants = single_product.variants.filter(is_active=True)
    variants_json = json.dumps([
        {
            'id':    v.id,
            'color': v.color,
            'size':  v.size,
            'price': float(v.effective_price),
            'stock': v.stock,
        }
        for v in active_variants
    ])

    # Auto-select the first available variant (lowest price) for default display
    first_variant = active_variants.order_by('price').first()
    default_price = float(first_variant.effective_price) if first_variant else None
    default_size  = first_variant.size if first_variant else None

    # ── Gallery grouped by colour ─────────────────────
    gallery_by_color = defaultdict(list)
    for img in product_gallery:
        gallery_by_color[img.color].append(img.image.url)

    gallery_by_color_json = json.dumps(dict(gallery_by_color))

    context = {
        'single_product':        single_product,
        'in_cart':               in_cart,
        'orderproduct':          orderproduct,
        'reviews':               reviews,
        'product_gallery':       product_gallery,
        'colors':                single_product.available_colors(),
        'sizes':                 single_product.available_sizes(),
        'variants_json':         variants_json,
        'default_price':         default_price,
        'default_size':          default_size,
        'gallery_by_color_json': gallery_by_color_json,
    }
    return render(request, 'product_detail.html', context)


def search(request):
    products = Product.objects.none()
    products_count = 0
    keyword = request.GET.get('keyword', '')

    if keyword:
        products = Product.objects.order_by('-created_date').filter(
            Q(description__icontains=keyword) |
            Q(product_name__icontains=keyword)
        ).annotate(min_variant_price=Min('variants__price'))
        products_count = products.count()

    # ── Scoped to matched products only ──────────────
    available_sizes = ProductVariant.objects.filter(
        is_active=True,
        product__in=products            # ← scoped to search results
    ).exclude(size='').values_list('size', flat=True).distinct().order_by('size')

    available_colors = ProductVariant.objects.filter(
        is_active=True,
        product__in=products            # ← scoped to search results
    ).exclude(color='').values_list('color', flat=True).distinct().order_by('color')

    context = {
        'products':         products,
        'products_count':   products_count,
        'available_sizes':  available_sizes,
        'available_colors': available_colors,
        'selected_sizes':   [],
        'selected_colors':  [],
        'min_price':        '',
        'max_price':        '',
    }
    return render(request, 'store.html', context)


def submit_review(request, product_id):
    if request.method == 'POST':
        try:
            review = ReviewRating.objects.get(
                user__id=request.user.id,
                product__id=product_id
            )
            review.subject = request.POST.get('subject')
            review.rating  = request.POST.get('rating')
            review.review  = request.POST.get('review')
            review.save()
            messages.success(request, 'Review updated.')
            return redirect(request.META.get('HTTP_REFERER'))

        except ReviewRating.DoesNotExist:
            data            = ReviewRating()
            data.subject    = request.POST.get('subject')
            data.rating     = request.POST.get('rating')
            data.review     = request.POST.get('review')
            data.ip         = request.META.get('REMOTE_ADDR')
            data.product_id = product_id
            data.user_id    = request.user.id
            data.save()
            messages.success(request, 'Thank you for submitting your review.')
            return redirect(request.META.get('HTTP_REFERER'))


def seller_store(request, shop_slug):
    shop = Shop.objects.get(slug=shop_slug)
    products = Product.objects.filter(
        shop=shop, is_available=True
    ).annotate(min_variant_price=Min('variants__price'))

    products_count = products.count()

    # ── Available filter options scoped to this shop's products ──
    available_sizes = ProductVariant.objects.filter(
        is_active=True,
        product__in=products            # ← scoped to this seller's products
    ).exclude(size='').values_list('size', flat=True).distinct().order_by('size')

    available_colors = ProductVariant.objects.filter(
        is_active=True,
        product__in=products            # ← scoped to this seller's products
    ).exclude(color='').values_list('color', flat=True).distinct().order_by('color')

    paginator = Paginator(products.order_by('id'), 9)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    context = {
        'shop':             shop,
        'products':         paged_products,
        'products_count':   products_count,
        'available_sizes':  available_sizes,
        'available_colors': available_colors,
        'selected_sizes':   [],
        'selected_colors':  [],
        'min_price':        '',
        'max_price':        '',
    }
    return render(request, 'seller_store.html', context)