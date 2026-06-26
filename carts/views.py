from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.models import UserProfile
from carts.models import Cart, CartItem
from store.models import Product, ProductVariant
from django.contrib.auth.decorators import login_required

# Create your views here.
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def _resolve_variant(request, product):
    variant_id = request.POST.get('variant_id') or request.GET.get('variant_id')

    if not variant_id:
        if product.has_variants():
            return None, 'Please select an option before adding to your bag.'
        return None, None

    variant = ProductVariant.objects.filter(id=variant_id, product=product).first()
    if not variant or not variant.is_active:
        return None, 'That option is no longer available.'
    if variant.stock <= 0:
        return None, 'That option is out of stock.'
    return variant, None


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    current_user = request.user

    variant, error = _resolve_variant(request, product)
    if error:
        messages.error(request, error)
        return redirect(product.get_url())

    if current_user.is_authenticated:
        cart_item = CartItem.objects.filter(product=product, variant=variant, user=current_user).first()
        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
        else:
            CartItem.objects.create(product=product, variant=variant, quantity=1, user=current_user)
    else:
        cart, _created = Cart.objects.get_or_create(cart_id=_cart_id(request))
        cart_item = CartItem.objects.filter(product=product, variant=variant, cart=cart).first()
        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
        else:
            CartItem.objects.create(product=product, variant=variant, quantity=1, cart=cart)

    return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    product = Product.objects.get(id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def clear_cart(request, product_id, cart_item_id):
    product = Product.objects.get(id=product_id)
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, product=product, id=cart_item_id)
    cart_items.delete()
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            unit_price = cart_item.variant.effective_price if cart_item.variant else cart_item.product.price
            total    += unit_price * cart_item.quantity
            quantity += cart_item.quantity
        tax         = round((2 * total) / 100, 2)
        grand_total = round(total + tax, 2)
    except Cart.DoesNotExist:
        pass

    context = {
        'total':       total,
        'quantity':    quantity,
        'cart_items':  cart_items,
        'tax':         tax,
        'grand_total': grand_total,
    }
    return render(request, 'cart.html', context=context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            unit_price = cart_item.variant.effective_price if cart_item.variant else cart_item.product.price
            total    += unit_price * cart_item.quantity
            quantity += cart_item.quantity
        tax         = round((2 * total) / 100, 2)   # ← round
        grand_total = round(total + tax, 2)           # ← round
    except Cart.DoesNotExist:
        pass

    userprofile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'total':       total,
        'quantity':    quantity,
        'cart_items':  cart_items,
        'tax':         tax,
        'grand_total': grand_total,
        'userprofile': userprofile,
    }
    return render(request, 'checkout.html', context=context)