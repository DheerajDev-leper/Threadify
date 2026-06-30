from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Sum, Count, Avg, Q, FloatField
from django.db.models.functions import Cast
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import json

from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST

from store.models import Product, ProductVariant, ReviewRating, ProductGallery
from store.models import Shop
from category.models import Category
from accounts.models import Account, UserProfile
from orders.models import Order, OrderProduct, Payment


# ─── Access helpers ───────────────────────────────────────────────────────────

def is_any_admin(user):
    """Allows both super admins and approved shop owners."""
    return (
        user.is_authenticated and
        user.is_admin and
        getattr(user, 'is_any_admin', False)
    )

def is_super_admin(user):
    return user.is_authenticated and getattr(user, 'is_super_admin', False)

def role_required(*roles):
    def check(user):
        return user.is_authenticated and user.role in roles
    return user_passes_test(check, login_url='admin_login')


# ─── Login / Register ─────────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated and getattr(request.user, 'is_any_admin', False):
        return redirect('admin_dashboard')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, 'No account found with those credentials.')
        elif not getattr(user, 'is_any_admin', False):
            messages.error(request, 'You do not have admin access.')
        elif user.role == 'shop_owner':
            shop = getattr(user, 'shop', None)
            if shop is None:
                messages.error(request, 'No shop linked to your account. Contact support.')
            elif not shop.is_approved:
                messages.error(request, 'Your shop is pending approval by the super admin.')
            else:
                auth_login(request, user)
                return redirect('admin_dashboard')
        else:
            auth_login(request, user)
            return redirect('admin_dashboard')

    return render(request, 'admin_panel/login.html', {})


def admin_logout(request):
    auth_logout(request)
    return redirect('admin_login')


def admin_forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = Account.objects.get(email=email)
            if not getattr(user, 'is_any_admin', False):
                pass
            else:
                uid   = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse('admin_reset_password', kwargs={'uidb64': uid, 'token': token})
                )
                send_mail(
                    subject = 'StyleAdmin — Password Reset',
                    message = (
                        f"Hi {user.first_name},\n\n"
                        f"Click the link below to reset your StyleAdmin password:\n\n"
                        f"{reset_url}\n\n"
                        f"This link expires in 1 hour. If you didn't request this, ignore this email.\n\n"
                        f"— StyleAdmin"
                    ),
                    from_email = settings.DEFAULT_FROM_EMAIL,
                    recipient_list = [email],
                    fail_silently = True,
                )
        except Account.DoesNotExist:
            pass

        return render(request, 'admin_panel/password/forgot_password_done.html', {'email': email})

    return render(request, 'admin_panel/password/forgot_password.html')


def admin_reset_password(request, uidb64, token):
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (Account.DoesNotExist, ValueError, TypeError):
        user = None

    token_valid = user is not None and default_token_generator.check_token(user, token)

    if not token_valid:
        return render(request, 'admin_panel/password/reset_password_invalid.html')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        else:
            user.set_password(password1)
            user.save()
            messages.success(request, 'Password updated successfully. Please sign in.')
            return redirect('admin_login')

    return render(request, 'admin_panel/password/reset_password.html', {
        'uidb64': uidb64,
        'token':  token,
    })


def shop_register(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        email       = request.POST.get('email', '').strip()
        phone       = request.POST.get('phone', '').strip()
        password    = request.POST.get('password', '')
        password2   = request.POST.get('password2', '')
        shop_name   = request.POST.get('shop_name', '').strip()
        shop_desc   = request.POST.get('shop_description', '').strip()

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'admin_panel/shop_register.html', {'post': request.POST})

        if Account.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'admin_panel/shop_register.html', {'post': request.POST})

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'admin_panel/shop_register.html', {'post': request.POST})

        import re
        slug = re.sub(r'[^a-z0-9]+', '-', shop_name.lower()).strip('-')
        if Shop.objects.filter(slug=slug).exists():
            slug = f"{slug}-{Account.objects.count()}"

        user = Account.objects.create_user(
            first_name = first_name,
            last_name  = last_name,
            email      = email,
            username   = email.split('@')[0],
            password   = password,
        )
        user.phone_number = phone
        user.role     = 'shop_owner'
        user.is_admin = True
        user.is_active = True
        user.save()

        Shop.objects.create(
            owner       = user,
            name        = shop_name,
            slug        = slug,
            description = shop_desc,
            is_approved = False,
        )

        send_mail(
            subject    = 'StyleAdmin — Shop Registration Received',
            message    = (
                f"Hi {first_name},\n\n"
                f"Thanks for registering your shop \"{shop_name}\" on StyleAdmin.\n\n"
                f"Your application is currently under review. Our team will verify your details "
                f"and you'll receive another email once your shop is approved.\n\n"
                f"In the meantime, if you have any questions feel free to reply to this email.\n\n"
                f"— The StyleAdmin Team"
            ),
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [email],
            fail_silently  = True,
        )

        messages.success(
            request,
            'Registration successful! Your account is pending approval. '
            'You will be notified once the super admin approves your shop.'
        )
        return redirect('admin_login')

    return render(request, 'admin_panel/shop_register.html', {})


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def admin_dashboard(request):
    today           = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago  = today - timedelta(days=7)
    is_super        = request.user.is_super_admin

    if is_super:
        orders_qs   = Order.objects.filter(is_ordered=True)
        products_qs = Product.objects.all()
    else:
        shop        = request.user.shop
        products_qs = Product.objects.filter(shop=shop)
        product_ids = products_qs.values_list('id', flat=True)
        order_ids   = OrderProduct.objects.filter(
                          ordered=True, product__in=product_ids
                      ).values_list('order_id', flat=True).distinct()
        orders_qs   = Order.objects.filter(id__in=order_ids, is_ordered=True)

    total_revenue   = orders_qs.aggregate(total=Sum('order_total'))['total'] or 0
    total_orders    = orders_qs.count()
    total_products  = products_qs.count()
    total_customers = (
        Account.objects.filter(is_admin=False).count()
        if is_super else
        orders_qs.values('user').distinct().count()
    )

    revenue_30 = (
        orders_qs
        .filter(created_at__date__gte=thirty_days_ago)
        .aggregate(total=Sum('order_total'))['total'] or 0
    )

    daily_orders = []
    daily_labels = []
    for i in range(6, -1, -1):
        day   = today - timedelta(days=i)
        count = orders_qs.filter(created_at__date=day).count()
        daily_orders.append(count)
        daily_labels.append(day.strftime('%a'))

    monthly_revenue = []
    monthly_labels  = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)
        rev = (
            orders_qs
            .filter(created_at__date__gte=month_start, created_at__date__lt=month_end)
            .aggregate(total=Sum('order_total'))['total'] or 0
        )
        monthly_revenue.append(float(rev))
        monthly_labels.append(month_start.strftime('%b %Y'))

    status_data   = orders_qs.values('status').annotate(count=Count('id'))
    status_labels = [s['status'] for s in status_data]
    status_counts = [s['count'] for s in status_data]

    op_filter = {'ordered': True}
    if not is_super:
        op_filter['product__in'] = product_ids
    top_products = (
        OrderProduct.objects
        .filter(**op_filter)
        .values('product__product_name')
        .annotate(total_sold=Sum('quantity'), revenue=Sum('product_price'))
        .order_by('-total_sold')[:5]
    )

    recent_orders = orders_qs.order_by('-created_at')[:8]
    low_stock     = products_qs.filter(stock__lte=5).order_by('stock')[:5]

    pending_shops = (
        Shop.objects.filter(is_approved=False).select_related('owner')
        if is_super else []
    )

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
        'pending_shops'   : pending_shops,
        'is_super'        : is_super,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─── Products ─────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def product_list(request):
    query    = request.GET.get('q', '')
    category = request.GET.get('category', '')
    stock    = request.GET.get('stock', '')

    if request.user.is_super_admin:
        products = Product.objects.select_related('category', 'shop').order_by('-created_date')
    else:
        products = Product.objects.filter(
            shop=request.user.shop
        ).select_related('category').order_by('-created_date')

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
    products  = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.all()

    return render(request, 'admin_panel/products/list.html', {
        'products'   : products,
        'categories' : categories,
        'query'      : query,
        'is_super'   : request.user.is_super_admin,
    })


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
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

        if request.user.is_super_admin:
            shop_id = request.POST.get('shop') or None
            shop    = Shop.objects.get(pk=shop_id) if shop_id else None
        else:
            shop = getattr(request.user, 'shop', None)
            if shop is None:
                messages.error(request, 'No shop linked to your account. Contact the super admin.')
                return redirect('admin_login')

        product = Product.objects.create(
            product_name = product_name,
            slug         = slug,
            description  = description,
            price        = 0,
            stock        = stock or 0,
            category_id  = category_id,
            is_available = is_available,
            Image        = image,
            shop         = shop,
        )
        messages.success(request, f'Product "{product.product_name}" added successfully.')
        return redirect('admin_product_list')

    shops = Shop.objects.filter(is_approved=True) if request.user.is_super_admin else None
    return render(request, 'admin_panel/products/form.html', {
        'categories' : categories,
        'action'     : 'Add',
        'shops'      : shops,
        'is_super'   : request.user.is_super_admin,
    })


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if not request.user.is_super_admin and product.shop != request.user.shop:
        messages.error(request, 'You do not have permission to edit this product.')
        return redirect('admin_product_list')

    categories = Category.objects.all()
    variants   = ProductVariant.objects.filter(product=product)

    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product.slug         = request.POST.get('slug')
        product.description  = request.POST.get('description')
        product.category_id  = request.POST.get('category')
        product.is_available = request.POST.get('is_available') == 'on'
        if request.FILES.get('Image'):
            product.Image = request.FILES['Image']
        product.save()
        messages.success(request, f'Product "{product.product_name}" updated.')
        return redirect('admin_product_list')

    available_colors = (
        ProductVariant.objects
        .filter(product=product, is_active=True)
        .exclude(color='')
        .values_list('color', flat=True)
        .distinct()
        .order_by('color')
    )

    return render(request, 'admin_panel/products/form.html', {
        'product'          : product,
        'categories'       : categories,
        'variants'         : variants,
        'product_gallery'  : ProductGallery.objects.filter(product=product),
        'action'           : 'Edit',
        'is_super'         : request.user.is_super_admin,
        'available_colors' : available_colors,
    })


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not request.user.is_super_admin and product.shop != request.user.shop:
        messages.error(request, 'You do not have permission to delete this product.')
        return redirect('admin_product_list')
    if request.method == 'POST':
        name = product.product_name
        product.delete()
        messages.success(request, f'Product "{name}" deleted.')
        return redirect('admin_product_list')
    return render(request, 'admin_panel/products/confirm_delete.html', {
        'object': product, 'type': 'Product'
    })


# ─── Variant stock/price sync helper ──────────────────────────────────────────

def _sync_product_from_variants(product):
    """
    Recalculate product.stock and product.price from its active variants.
    Called after every variant add / edit / delete so the parent product
    always reflects the true aggregated values.
    """
    variants = ProductVariant.objects.filter(product=product, is_active=True)
    product.stock = sum(v.stock for v in variants)
    prices = [v.price for v in variants if v.price is not None]
    product.price = min(prices) if prices else 0
    product.save(update_fields=['stock', 'price'])


# ─── Variants ─────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def variant_add(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)

    if not request.user.is_super_admin and product.shop != request.user.shop:
        messages.error(request, 'Permission denied.')
        return redirect('admin_product_list')

    if request.method == 'POST':
        try:
            ProductVariant.objects.create(
                product   = product,
                color     = request.POST.get('color', '').strip(),
                size      = request.POST.get('size', '').strip(),
                sku       = request.POST.get('sku', '').strip(),
                stock     = request.POST.get('stock') or 0,
                price     = request.POST.get('price') or None,
                is_active = request.POST.get('is_active') == 'on',
            )
            _sync_product_from_variants(product)
            messages.success(request, 'Variant added.')

        except IntegrityError:
            messages.error(
                request,
                'A variant with that colour/size combination already exists.'
            )

    return redirect('admin_product_edit', pk=product_pk)


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def variant_edit(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    if not request.user.is_super_admin and variant.product.shop != request.user.shop:
        messages.error(request, 'Permission denied.')
        return redirect('admin_product_list')

    if request.method == 'POST':
        variant.color     = request.POST.get('color', '').strip()
        variant.size      = request.POST.get('size', '').strip()
        variant.sku       = request.POST.get('sku', '').strip()
        variant.stock     = request.POST.get('stock') or 0
        variant.price     = request.POST.get('price') or None
        variant.is_active = request.POST.get('is_active') == 'on'
        try:
            variant.save()
            _sync_product_from_variants(variant.product)  # ← FIX: sync after edit
            messages.success(request, 'Variant updated.')
        except IntegrityError:
            messages.error(request, 'A variant with that colour/size combination already exists.')

    return redirect('admin_product_edit', pk=variant.product.pk)


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def variant_delete(request, pk):
    variant    = get_object_or_404(ProductVariant, pk=pk)
    product    = variant.product                          # ← FIX: capture before deleting
    product_pk = product.pk
    if not request.user.is_super_admin and product.shop != request.user.shop:
        messages.error(request, 'Permission denied.')
        return redirect('admin_product_list')
    variant.delete()
    _sync_product_from_variants(product)                  # ← FIX: sync after delete
    messages.success(request, 'Variant deleted.')
    return redirect('admin_product_edit', pk=product_pk)


# ─── Gallery ──────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def gallery_add(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    if not request.user.is_super_admin and product.shop != request.user.shop:
        messages.error(request, 'Permission denied.')
        return redirect('admin_product_list')
    if request.method == 'POST':
        images = request.FILES.getlist('gallery_images')
        if not images:
            messages.warning(request, 'No images selected.')
            return redirect('admin_product_edit', pk=product_pk)
        color = request.POST.get('color', '').strip()
        for img in images:
            ProductGallery.objects.create(
                product = product,
                image   = img,
                color   = color,
            )
        messages.success(request, f'{len(images)} photo(s) added to gallery.')
    return redirect('admin_product_edit', pk=product_pk)


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def gallery_delete(request, pk):
    gallery_img = get_object_or_404(ProductGallery, pk=pk)
    product_pk  = gallery_img.product.pk
    if not request.user.is_super_admin and gallery_img.product.shop != request.user.shop:
        messages.error(request, 'Permission denied.')
        return redirect('admin_product_list')
    storage = gallery_img.image.storage
    if storage.exists(gallery_img.image.name):
        storage.delete(gallery_img.image.name)
    gallery_img.delete()
    messages.success(request, 'Photo removed.')
    return redirect('admin_product_edit', pk=product_pk)


# ─── Categories (super admin only) ────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('product')).order_by('category_name')
    return render(request, 'admin_panel/categories/list.html', {'categories': categories})


@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
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
@user_passes_test(is_super_admin, login_url='admin_login')
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
    return render(request, 'admin_panel/categories/form.html', {
        'category': category, 'action': 'Edit'
    })


@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('admin_category_list')
    return render(request, 'admin_panel/products/confirm_delete.html', {
        'object': category, 'type': 'Category'
    })


# ─── Orders ───────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def order_list(request):
    status = request.GET.get('status', '')
    query  = request.GET.get('q', '')

    if request.user.is_super_admin:
        orders = Order.objects.filter(is_ordered=True).select_related('user', 'payment')
    else:
        product_ids = Product.objects.filter(
            shop=request.user.shop
        ).values_list('id', flat=True)
        order_ids = OrderProduct.objects.filter(
            ordered=True, product__in=product_ids
        ).values_list('order_id', flat=True).distinct()
        orders = Order.objects.filter(
            id__in=order_ids, is_ordered=True
        ).select_related('user', 'payment')

    if status:
        orders = orders.filter(status=status)
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |
            Q(first_name__icontains=query)   |
            Q(last_name__icontains=query)    |
            Q(email__icontains=query)
        )

    orders = orders.order_by('-created_at')
    paginator = Paginator(orders, 15)
    orders    = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_panel/orders/list.html', {
        'orders'         : orders,
        'status_filter'  : status,
        'status_choices' : Order.STATUS,
        'is_super'       : request.user.is_super_admin,
    })


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def order_detail(request, pk):
    order          = get_object_or_404(Order, pk=pk)
    order_products = OrderProduct.objects.filter(order=order).select_related('product')

    if not request.user.is_super_admin:
        order_products = order_products.filter(product__shop=request.user.shop)

    if request.method == 'POST' and request.user.is_super_admin:
        order.status = request.POST.get('status')
        order.save()
        messages.success(request, f'Order #{order.order_number} updated.')
        return redirect('admin_order_detail', pk=pk)

    return render(request, 'admin_panel/orders/detail.html', {
        'order'          : order,
        'order_products' : order_products,
        'status_choices' : Order.STATUS,
        'is_super'       : request.user.is_super_admin,
    })


# ─── Customers (super admin only) ─────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
def customer_list(request):
    query     = request.GET.get('q', '')
    buyer_ids = Order.objects.filter(is_ordered=True).values_list('user_id', flat=True).distinct()

    customers = Account.objects.filter(
        id__in=buyer_ids
    ).exclude(
        role='super_admin'
    ).order_by('-date_joined')

    if query:
        customers = customers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)  |
            Q(email__icontains=query)
        )
    paginator = Paginator(customers, 15)
    customers = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/customers/list.html', {
        'customers': customers, 'query': query
    })


@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
def customer_detail(request, pk):
    customer    = get_object_or_404(Account, pk=pk)
    orders      = Order.objects.filter(user=customer, is_ordered=True).order_by('-created_at')
    total_spent = orders.aggregate(total=Sum('order_total'))['total'] or 0
    reviews     = ReviewRating.objects.filter(user=customer)
    try:
        profile = customer.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    return render(request, 'admin_panel/customers/detail.html', {
        'customer'   : customer,
        'orders'     : orders,
        'total_spent': total_spent,
        'reviews'    : reviews,
        'profile'    : profile,
    })


@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
def customer_toggle(request, pk):
    customer = get_object_or_404(Account, pk=pk)
    customer.is_active = not customer.is_active
    customer.save()
    state = 'activated' if customer.is_active else 'deactivated'
    messages.success(request, f'Account {state}.')
    return redirect('admin_customer_list')


# ─── Shop Owners (super admin only) ───────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
def shop_owner_list(request):
    shops = Shop.objects.select_related('owner').order_by('-owner__date_joined')
    return render(request, 'admin_panel/shop_owners/list.html', {'shops': shops})


@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
def shop_approve(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    shop.is_approved = True
    shop.save()
    login_url = request.build_absolute_uri(reverse('admin_login'))
    send_mail(
        subject    = 'StyleAdmin — Your Shop Has Been Approved! 🎉',
        message    = (
            f"Hi {shop.owner.first_name},\n\n"
            f"Great news — your shop \"{shop.name}\" has been approved by our team!\n\n"
            f"You can now sign in to your StyleAdmin dashboard and start adding products:\n"
            f"{login_url}\n\n"
            f"If you have any questions, feel free to reach out.\n\n"
            f"— The StyleAdmin Team"
        ),
        from_email     = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [shop.owner.email],
        fail_silently  = True,
    )
    messages.success(request, f'"{shop.name}" has been approved.')
    return redirect('admin_shop_owner_list')


@login_required(login_url='admin_login')
@user_passes_test(is_super_admin, login_url='admin_login')
def shop_reject(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    if request.method == 'POST':
        shop.owner.is_active = False
        shop.owner.save()
        shop.delete()
        messages.success(request, 'Shop rejected and account deactivated.')
        return redirect('admin_shop_owner_list')
    return render(request, 'admin_panel/products/confirm_delete.html', {
        'object': shop, 'type': 'Shop Application'
    })


# ─── Reports ──────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def reports(request):
    today      = timezone.now().date()
    range_days = int(request.GET.get('range', 30))
    start_date = today - timedelta(days=range_days)
    is_super   = request.user.is_super_admin

    if is_super:
        orders = Order.objects.filter(is_ordered=True, created_at__date__gte=start_date)
        op_qs  = OrderProduct.objects.filter(ordered=True, created_at__date__gte=start_date)
    else:
        product_ids = Product.objects.filter(
            shop=request.user.shop
        ).values_list('id', flat=True)
        order_ids = OrderProduct.objects.filter(
            ordered=True, product__in=product_ids
        ).values_list('order_id', flat=True).distinct()
        orders = Order.objects.filter(
            id__in=order_ids, is_ordered=True, created_at__date__gte=start_date
        )
        op_qs = OrderProduct.objects.filter(
            ordered=True, product__in=product_ids, created_at__date__gte=start_date
        )

    total_revenue = orders.aggregate(total=Sum('order_total'))['total'] or 0
    total_orders  = orders.count()
    avg_order_val = orders.aggregate(avg=Avg('order_total'))['avg'] or 0
    total_tax     = orders.aggregate(total=Sum('tax'))['total'] or 0

    daily_data = []
    for i in range(range_days - 1, -1, -1):
        day = today - timedelta(days=i)
        rev = (
            orders.filter(created_at__date=day)
            .aggregate(total=Sum('order_total'))['total'] or 0
        )
        daily_data.append({'date': day.strftime('%d %b'), 'revenue': float(rev)})

    top_products = (
        op_qs
        .values('product__product_name')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('product_price'))
        .order_by('-total_rev')[:10]
    )

    top_categories = (
        op_qs
        .values('product__category__category_name')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('product_price'))
        .order_by('-total_rev')[:5]
    )

    payment_methods = (
        Payment.objects
        .filter(created_at__date__gte=start_date)
        .values('payment_method')
        .annotate(
            count=Count('id'),
            total=Sum(Cast('amount_paid', output_field=FloatField())),
        )
    ) if is_super else []

    return render(request, 'admin_panel/reports.html', {
        'total_revenue'   : total_revenue,
        'total_orders'    : total_orders,
        'avg_order_val'   : round(avg_order_val, 2),
        'total_tax'       : total_tax,
        'range_days'      : range_days,
        'daily_data'      : json.dumps(daily_data),
        'top_products'    : top_products,
        'top_categories'  : top_categories,
        'payment_methods' : payment_methods,
        'is_super'        : is_super,
    })


# ─── Reviews ──────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def review_list(request):
    if request.user.is_super_admin:
        reviews = ReviewRating.objects.select_related('product', 'user').order_by('-created_at')
    else:
        product_ids = Product.objects.filter(
            shop=request.user.shop
        ).values_list('id', flat=True)
        reviews = ReviewRating.objects.filter(
            product__in=product_ids
        ).select_related('product', 'user').order_by('-created_at')

    paginator = Paginator(reviews, 20)
    reviews   = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/reviews/list.html', {'reviews': reviews})


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def review_toggle(request, pk):
    review = get_object_or_404(ReviewRating, pk=pk)
    if not request.user.is_super_admin and review.product.shop != request.user.shop:
        messages.error(request, 'Permission denied.')
        return redirect('admin_review_list')
    review.status = not review.status
    review.save()
    messages.success(request, 'Review status updated.')
    return redirect('admin_review_list')


@login_required(login_url='admin_login')
@user_passes_test(is_any_admin, login_url='admin_login')
def review_delete(request, pk):
    review = get_object_or_404(ReviewRating, pk=pk)
    if not request.user.is_super_admin and review.product.shop != request.user.shop:
        messages.error(request, 'Permission denied.')
        return redirect('admin_review_list')
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted.')
        return redirect('admin_review_list')
    return render(request, 'admin_panel/products/confirm_delete.html', {
        'object': review, 'type': 'Review'
    })


@staff_member_required
@require_POST
def admin_gallery_color(request, pk):
    img = get_object_or_404(ProductGallery, pk=pk)
    img.color = request.POST.get('color', '').strip()
    img.save(update_fields=['color'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponse(status=200)
    return redirect(request.META.get('HTTP_REFERER', '/'))