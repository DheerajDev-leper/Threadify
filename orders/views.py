import datetime
import json

import razorpay
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from carts.models import CartItem
from orders.models import Order, OrderProduct, Payment
from .forms import OrderForm

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)

    if cart_items.count() <= 0:
        return redirect('store')

    tax = 0
    grand_total = 0

    for cart_item in cart_items:
        variation_price = cart_item.variation.filter(price__isnull=False).values_list('price', flat=True).first()
        unit_price = variation_price if variation_price else cart_item.product.price
        total += unit_price * cart_item.quantity
        quantity += cart_item.quantity

    tax = round((2 * total) / 100, 2)
    grand_total = round(total + tax, 2)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            current_date = datetime.date.today().strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(
                user=current_user,
                is_ordered=False,
                order_number=order_number
            )

            # Create Razorpay order (amount in paise)
            razorpay_order = razorpay_client.order.create({
                'amount': int(grand_total * 100),
                'currency': 'INR',
                'receipt': order_number,
                'payment_capture': 1,
            })

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_amount': int(grand_total * 100),
            }
            return render(request, 'payments.html', context)

    return redirect('checkout')


@csrf_exempt
def payments(request):
    body = json.loads(request.body)

    try:
        order = Order.objects.get(
            user=request.user,
            is_ordered=False,
            order_number=body['orderID']
        )
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=400)

    payment_method = body.get('payment_method', 'Razorpay')

    if payment_method == 'COD':
        trans_id = 'COD'
        status = 'COMPLETED'
    else:
        # Verify Razorpay signature
        razorpay_payment_id = body.get('razorpay_payment_id', '')
        razorpay_order_id   = body.get('razorpay_order_id', '')
        razorpay_signature  = body.get('razorpay_signature', '')

        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id':   razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature':  razorpay_signature,
            })
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'error': 'Invalid payment signature'}, status=400)

        trans_id = razorpay_payment_id
        status   = 'COMPLETED'

    payment = Payment.objects.create(
        user=request.user,
        payment_id=trans_id,
        payment_method=payment_method,
        amount_paid=order.order_total,
        status=status,
    )

    order.payment = payment
    order.is_ordered = True
    order.save()

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        variation_price = item.variation.filter(price__isnull=False).values_list('price', flat=True).first()
        unit_price = variation_price if variation_price else item.product.price

        orderproduct = OrderProduct.objects.create(
            order_id=order.id,
            payment=payment,
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            product_price=unit_price,
            ordered=True,
        )
        orderproduct.variation.set(item.variation.all())

        product = item.product
        product.stock -= item.quantity
        product.save()

    cart_items.delete()

    mail_subject = 'Thank you for your order!'
    message = render_to_string('order_received_email.html', {
        'user': request.user,
        'order': order,
    })
    EmailMessage(mail_subject, message, to=[request.user.email]).send()

    return JsonResponse({
        'order_number': order.order_number,
        'transID': trans_id,
    })


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = sum(
            item.product_price * item.quantity
            for item in ordered_products
        )

        payment = order.payment

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': transID,
            'payment': payment,
            'subtotal': subtotal,
            'cart_items': ordered_products,
        }
        return render(request, 'order_complete.html', context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')