from django.contrib import messages
from django.shortcuts import redirect, render

from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from django.db.models import Q

from orders.models import OrderProduct

from .forms import ReviewForm
from .models import Product, ProductGallery, ReviewRating, Variation
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
            variation__variation_category='size',
            variation__variation_value__in=selected_sizes,
            variation__is_active=True
        ).distinct()

    # ── Color filter ─────────────────────────────────
    selected_colors = request.GET.getlist('color')
    if selected_colors:
        products = products.filter(
            variation__variation_category='color',
            variation__variation_value__in=selected_colors,
            variation__is_active=True
        ).distinct()

    # ── Price range filter ───────────────────────────
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # ── Count before pagination ──────────────────────
    products_count = products.count()

    # ── Pagination ───────────────────────────────────
    products = products.order_by('id')
    per_page = 3 if category_slug else 9
    paginator = Paginator(products, per_page)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # ── Available filter options (for the drawer) ────
    # Get all sizes and colors that exist for available products
    available_sizes = Variation.objects.filter(
        variation_category='size',
        is_active=True,
        product__is_available=True
    ).values_list('variation_value', flat=True).distinct().order_by('variation_value')

    available_colors = Variation.objects.filter(
        variation_category='color',
        is_active=True,
        product__is_available=True
    ).values_list('variation_value', flat=True).distinct().order_by('variation_value')

    context = {
        'products':        paged_products,
        'products_count':  products_count,
        # filter options for the drawer
        'available_sizes':  available_sizes,
        'available_colors': available_colors,
        # currently selected (to keep pills highlighted)
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

    reviews        = ReviewRating.objects.filter(product_id=single_product.id, status=True)
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product':  single_product,
        'in_cart':         in_cart,
        'orderproduct':    orderproduct,
        'reviews':         reviews,
        'product_gallery': product_gallery,
    }
    return render(request, 'product_detail.html', context)


def search(request):
    products = Product.objects.none()
    products_count = 0
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) |
                Q(product_name__icontains=keyword)
            )
            products_count = products.count()

    # Reuse same filter options for search results page
    available_sizes = Variation.objects.filter(
        variation_category='size', is_active=True
    ).values_list('variation_value', flat=True).distinct()

    available_colors = Variation.objects.filter(
        variation_category='color', is_active=True
    ).values_list('variation_value', flat=True).distinct()

    context = {
        'products':        products,
        'products_count':  products_count,
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
            data         = ReviewRating()
            data.subject = request.POST.get('subject')
            data.rating  = request.POST.get('rating')
            data.review  = request.POST.get('review')
            data.ip      = request.META.get('REMOTE_ADDR')
            data.product_id = product_id
            data.user_id    = request.user.id
            data.save()
            messages.success(request, 'Thank you for submitting your review.')
            return redirect(request.META.get('HTTP_REFERER'))