from django.contrib import messages
from django.shortcuts import redirect, render

from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from django.db.models import Q

from orders.models import OrderProduct

from .forms import ReviewForm
from .models import Product, ProductGallery, ReviewRating
from django.core.paginator import Paginator


# Create your views here.
def store(request, category_slug=None):
    categories = None
    products = None
    if category_slug != None:
        categories = Category.objects.get(slug=category_slug)
        products = Product.objects.all().filter(is_available=True, category=categories)
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        products_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 9)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        products_count = products.count()
    context = {
        'products': paged_products,
        'products_count': products_count
        }
    return render(request, 'store.html', context)

def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e
    
    if request.user.is_authenticated:
         try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
         except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    #product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    }
    return render(request, 'product_detail.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            products_count = products.count()
    context = {
        'products': products,
        'products_count': products_count,
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
            review.rating = request.POST.get('rating')
            review.review = request.POST.get('review')
            review.save()

            messages.success(request, 'Review updated.')
            return redirect(request.META.get('HTTP_REFERER'))

        except ReviewRating.DoesNotExist:
            data = ReviewRating()
            data.subject = request.POST.get('subject')
            data.rating = request.POST.get('rating')
            data.review = request.POST.get('review')
            data.ip = request.META.get('REMOTE_ADDR')
            data.product_id = product_id
            data.user_id = request.user.id
            data.save()

            messages.success(request, 'Thank you for submiting the review.')
            return redirect(request.META.get('HTTP_REFERER'))    