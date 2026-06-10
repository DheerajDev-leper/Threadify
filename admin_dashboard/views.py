from django.shortcuts import render
from orders.models import Order, OrderProduct
from django.db.models import Sum
from store.models import Product
from accounts.models import Account

def admin_dashboard(request):
    total_earnings = Order.objects.filter(is_ordered=True).aggregate(total=Sum('order_total'))['total'] or 0
    total_orders = Order.objects.filter(is_ordered=True).count()
    total_products = Product.objects.count()
    total_customers = Account.objects.filter(is_active=True).count()
    ordered_products = OrderProduct.objects.select_related(
        'product', 'order'
    ).all()
    context = {
        'total_earnings': total_earnings,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_customers': total_customers,
        'order_products': ordered_products,
    }

    return render(request, 'admin/dashboard.html', context)

def admin_products(request):
    products = Product.objects.all()
    context = {
        'products': products,
    }
    return render(request, 'admin/products.html', context)


