from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import json

from store.models import Product, Variation, ReviewRating
from category.models import Category
from accounts.models import Account, UserProfile
from orders.models import Order, OrderProduct, Payment


# ─── Access Control ───────────────────────────────────────────────────────────

def is_admin(user):
    return user.is_authenticated and user.is_admin


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago  = today - timedelta(days=7)

    # Summary cards
    total_revenue   = Order.objects.filter(is_ordered=True).aggregate(total=Sum('order_total'))['total'] or 0
    total_orders    = Order.objects.filter(is_ordered=True).count()
    total_products  = Product.objects.count()
    total_customers = Account.objects.filter(is_admin=False).count()

    # Revenue last 30 days
    revenue_30 = (
        Order.objects
        .filter(is_ordered=True, created_at__date__gte=thirty_days_ago)
        .aggregate(total=Sum('order_total'))['total'] or 0
    )

    # Orders last 7 days (for sparkline)
    daily_orders = []
    daily_labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Order.objects.filter(is_ordered=True, created_at__date=day).count()
        daily_orders.append(count)
        daily_labels.append(day.strftime('%a'))

    # Monthly revenue (last 6 months) for chart
    monthly_revenue = []
    monthly_labels  = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)
        rev = (
            Order.objects
            .filter(is_ordered=True, created_at__date__gte=month_start, created_at__date__lt=month_end)
            .aggregate(total=Sum('order_total'))['total'] or 0
        )
        monthly_revenue.append(float(rev))
        monthly_labels.append(month_start.strftime('%b %Y'))

    # Order status breakdown
    status_data = (
        Order.objects
        .filter(is_ordered=True)
        .values('status')
        .annotate(count=Count('id'))
    )
    status_labels = [s['status'] for s in status_data]
    status_counts = [s['count'] for s in status_data]

    # Top selling products
    top_products = (
        OrderProduct.objects
        .filter(ordered=True)
        .values('product__product_name')
        .annotate(total_sold=Sum('quantity'), revenue=Sum('product_price'))
        .order_by('-total_sold')[:5]
    )

    # Recent orders
    recent_orders = Order.objects.filter(is_ordered=True).order_by('-created_at')[:8]

    # Low stock products
    low_stock = Product.objects.filter(stock__lte=5).order_by('stock')[:5]

    context = {
        'total_revenue'   : total_revenue,
        'total_orders'    : total_orders,
        'total_products'  : total_products,
        'total_customers' : total_customers,
        'revenue_30'      : revenue_30,
        'daily_orders'    : json.dumps(daily_orders),
        'daily_labels'    : json.dumps(daily_labels),
        'monthly_revenue' : json.dumps(monthly_revenue),
        'monthly_labels'  : json.dumps(monthly_labels),
        'status_labels'   : json.dumps(status_labels),
        'status_counts'   : json.dumps(status_counts),
        'top_products'    : top_products,
        'recent_orders'   : recent_orders,
        'low_stock'       : low_stock,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─── Products ─────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def product_list(request):
    query    = request.GET.get('q', '')
    category = request.GET.get('category', '')
    stock    = request.GET.get('stock', '')

    products = Product.objects.select_related('category').order_by('-created_date')

    if query:
        products = products.filter(
            Q(product_name__icontains=query) | Q(description__icontains=query)
        )
    if category:
        products = products.filter(category__slug=category)
    if stock == 'low':
        products = products.filter(stock__lte=5)
    elif stock == 'out':
        products = products.filter(stock=0)

    paginator = Paginator(products, 12)
    page      = request.GET.get('page')
    products  = paginator.get_page(page)

    categories = Category.objects.all()
    context = {
        'products'   : products,
        'categories' : categories,
        'query'      : query,
    }
    return render(request, 'admin_panel/products/list.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def product_add(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        slug         = request.POST.get('slug')
        description  = request.POST.get('description')
        price        = request.POST.get('price')
        stock        = request.POST.get('stock')
        category_id  = request.POST.get('category')
        is_available = request.POST.get('is_available') == 'on'
        image        = request.FILES.get('Image')

        if Product.objects.filter(slug=slug).exists():
            messages.error(request, 'A product with this slug already exists.')
            return render(request, 'admin_panel/products/form.html', {'categories': categories})

        product = Product.objects.create(
            product_name = product_name,
            slug         = slug,
            description  = description,
            price        = price,
            stock        = stock,
            category_id  = category_id,
            is_available = is_available,
            Image        = image,
        )
        messages.success(request, f'Product "{product.product_name}" added successfully.')
        return redirect('admin_product_list')

    return render(request, 'admin_panel/products/form.html', {'categories': categories, 'action': 'Add'})


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def product_edit(request, pk):
    product    = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    variations = Variation.objects.filter(product=product)

    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product.slug         = request.POST.get('slug')
        product.description  = request.POST.get('description')
        product.price        = request.POST.get('price')
        product.stock        = request.POST.get('stock')
        product.category_id  = request.POST.get('category')
        product.is_available = request.POST.get('is_available') == 'on'
        if request.FILES.get('Image'):
            product.Image = request.FILES['Image']
        product.save()
        messages.success(request, f'Product "{product.product_name}" updated.')
        return redirect('admin_product_list')

    context = {
        'product'    : product,
        'categories' : categories,
        'variations' : variations,
        'action'     : 'Edit',
    }
    return render(request, 'admin_panel/products/form.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.product_name
        product.delete()
        messages.success(request, f'Product "{name}" deleted.')
        return redirect('admin_product_list')
    return render(request, 'admin_panel/products/confirm_delete.html', {'object': product, 'type': 'Product'})


# ─── Variations ───────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def variation_add(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    if request.method == 'POST':
        Variation.objects.create(
            product            = product,
            variation_category = request.POST.get('variation_category'),
            variation_value    = request.POST.get('variation_value'),
            price              = request.POST.get('price') or None,
            is_active          = request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Variation added.')
    return redirect('admin_product_edit', pk=product_pk)


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def variation_delete(request, pk):
    variation = get_object_or_404(Variation, pk=pk)
    product_pk = variation.product.pk
    variation.delete()
    messages.success(request, 'Variation deleted.')
    return redirect('admin_product_edit', pk=product_pk)


# ─── Categories ───────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('product')).order_by('category_name')
    return render(request, 'admin_panel/categories/list.html', {'categories': categories})


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def category_add(request):
    if request.method == 'POST':
        Category.objects.create(
            category_name = request.POST.get('category_name'),
            slug          = request.POST.get('slug'),
            description   = request.POST.get('description'),
            cat_image     = request.FILES.get('cat_image'),
        )
        messages.success(request, 'Category added.')
        return redirect('admin_category_list')
    return render(request, 'admin_panel/categories/form.html', {'action': 'Add'})


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.category_name = request.POST.get('category_name')
        category.slug          = request.POST.get('slug')
        category.description   = request.POST.get('description')
        if request.FILES.get('cat_image'):
            category.cat_image = request.FILES['cat_image']
        category.save()
        messages.success(request, 'Category updated.')
        return redirect('admin_category_list')
    return render(request, 'admin_panel/categories/form.html', {'category': category, 'action': 'Edit'})


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('admin_category_list')
    return render(request, 'admin_panel/products/confirm_delete.html', {'object': category, 'type': 'Category'})


# ─── Orders ───────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def order_list(request):
    status = request.GET.get('status', '')
    query  = request.GET.get('q', '')

    orders = Order.objects.filter(is_ordered=True).select_related('user', 'payment').order_by('-created_at')

    if status:
        orders = orders.filter(status=status)
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |
            Q(first_name__icontains=query)   |
            Q(last_name__icontains=query)    |
            Q(email__icontains=query)
        )

    paginator = Paginator(orders, 15)
    orders    = paginator.get_page(request.GET.get('page'))

    context = {
        'orders'         : orders,
        'status_filter'  : status,
        'status_choices' : Order.STATUS,
    }
    return render(request, 'admin_panel/orders/list.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def order_detail(request, pk):
    order         = get_object_or_404(Order, pk=pk)
    order_products = OrderProduct.objects.filter(order=order).select_related('product')

    if request.method == 'POST':
        new_status   = request.POST.get('status')
        order.status = new_status
        order.save()
        messages.success(request, f'Order #{order.order_number} status updated to {new_status}.')
        return redirect('admin_order_detail', pk=pk)

    context = {
        'order'         : order,
        'order_products': order_products,
        'status_choices': Order.STATUS,
    }
    return render(request, 'admin_panel/orders/detail.html', context)


# ─── Customers ────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def customer_list(request):
    query     = request.GET.get('q', '')
    customers = Account.objects.filter(is_admin=False).order_by('-date_joined')

    if query:
        customers = customers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)  |
            Q(email__icontains=query)
        )

    paginator = Paginator(customers, 15)
    customers = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/customers/list.html', {'customers': customers, 'query': query})


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def customer_detail(request, pk):
    customer       = get_object_or_404(Account, pk=pk)
    orders         = Order.objects.filter(user=customer, is_ordered=True).order_by('-created_at')
    total_spent    = orders.aggregate(total=Sum('order_total'))['total'] or 0
    reviews        = ReviewRating.objects.filter(user=customer)
    try:
        profile = customer.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    context = {
        'customer'   : customer,
        'orders'     : orders,
        'total_spent': total_spent,
        'reviews'    : reviews,
        'profile'    : profile,
    }
    return render(request, 'admin_panel/customers/detail.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def customer_toggle_active(request, pk):
    customer = get_object_or_404(Account, pk=pk)
    customer.is_active = not customer.is_active
    customer.save()
    state = 'activated' if customer.is_active else 'deactivated'
    messages.success(request, f'Account {state}.')
    return redirect('admin_customer_list')


# ─── Reports ──────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def reports(request):
    today        = timezone.now().date()
    range_days   = int(request.GET.get('range', 30))
    start_date   = today - timedelta(days=range_days)

    orders = Order.objects.filter(is_ordered=True, created_at__date__gte=start_date)

    total_revenue = orders.aggregate(total=Sum('order_total'))['total'] or 0
    total_orders  = orders.count()
    avg_order_val = orders.aggregate(avg=Avg('order_total'))['avg'] or 0
    total_tax     = orders.aggregate(total=Sum('tax'))['total'] or 0

    # Daily revenue for chart
    daily_data = []
    for i in range(range_days - 1, -1, -1):
        day = today - timedelta(days=i)
        rev = (
            orders.filter(created_at__date=day)
            .aggregate(total=Sum('order_total'))['total'] or 0
        )
        daily_data.append({'date': day.strftime('%d %b'), 'revenue': float(rev)})

    # Top products in range
    top_products = (
        OrderProduct.objects
        .filter(ordered=True, created_at__date__gte=start_date)
        .values('product__product_name')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('product_price'))
        .order_by('-total_rev')[:10]
    )

    # Top categories
    top_categories = (
        OrderProduct.objects
        .filter(ordered=True, created_at__date__gte=start_date)
        .values('product__category__category_name')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('product_price'))
        .order_by('-total_rev')[:5]
    )

    # Payment methods
    payment_methods = (
        Payment.objects
        .filter(created_at__date__gte=start_date)
        .values('payment_method')
        .annotate(count=Count('id'), total=Sum('amount_paid'))
    )

    context = {
        'total_revenue'   : total_revenue,
        'total_orders'    : total_orders,
        'avg_order_val'   : round(avg_order_val, 2),
        'total_tax'       : total_tax,
        'range_days'      : range_days,
        'daily_data'      : json.dumps(daily_data),
        'top_products'    : top_products,
        'top_categories'  : top_categories,
        'payment_methods' : payment_methods,
    }
    return render(request, 'admin_panel/reports.html', context)


# ─── Reviews ──────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def review_list(request):
    reviews = ReviewRating.objects.select_related('product', 'user').order_by('-created_at')
    paginator = Paginator(reviews, 20)
    reviews   = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/reviews/list.html', {'reviews': reviews})


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def review_toggle(request, pk):
    review = get_object_or_404(ReviewRating, pk=pk)
    review.status = not review.status
    review.save()
    messages.success(request, 'Review status updated.')
    return redirect('admin_review_list')


@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def review_delete(request, pk):
    review = get_object_or_404(ReviewRating, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted.')
        return redirect('admin_review_list')
    return render(request, 'admin_panel/products/confirm_delete.html', {'object': review, 'type': 'Review'})


from django.contrib.auth import authenticate, login

def admin_login(request):
    if request.user.is_authenticated and request.user.is_admin:
        return redirect('admin_dashboard')
    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user and user.is_admin:
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'admin_panel/login.html', {})