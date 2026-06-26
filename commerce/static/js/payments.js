function getCookie(name) {
  let c = null;
  if (document.cookie && document.cookie !== '') {
    document.cookie.split(';').forEach(function(x) {
      x = x.trim();
      if (x.substring(0, name.length + 1) === (name + '=')) {
        c = decodeURIComponent(x.substring(name.length + 1));
      }
    });
  }
  return c;
}

const csrftoken = getCookie('csrftoken');
let selectedMethod = 'cod';
let paymentData = {};

function setPaymentData(data) {
  paymentData = data;
}

function selectMethod(method) {
  selectedMethod = method;
  document.getElementById('method-cod').classList.toggle('active',  method === 'cod');
  document.getElementById('method-card').classList.toggle('active', method === 'card');
  document.getElementById('cod-button').style.display = method === 'cod'  ? 'block' : 'none';
  document.getElementById('pay-button').style.display = method === 'card' ? 'block' : 'none';
}

document.addEventListener("DOMContentLoaded", function() {
  const orderID = paymentData.orderID || "";

  if (document.getElementById("cod-button")) {
    document.getElementById("cod-button").addEventListener("click", function(e) {
      e.preventDefault();
      fetch("/orders/payments/", {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
        body: JSON.stringify({
          orderID:        orderID,
          payment_method: "COD",
        })
      }).then(r => {
        if (!r.ok) throw new Error('Payment failed: ' + r.status);
        return r.json();
      }).then(data => {
        if (data.order_number) {
          window.location.href = "/orders/order_complete/?order_number=" + data.order_number + "&payment_id=" + data.transID;
        } else {
          console.error("Invalid response:", data);
          alert("Payment processing error. Please try again.");
        }
      }).catch(err => {
        console.error("COD Error:", err);
        alert("Error processing payment: " + err.message);
      });
    });
  }

  if (document.getElementById("pay-button") && window.Razorpay && paymentData.razorpayKey) {
    const rzpOptions = {
      key:         paymentData.razorpayKey,
      amount:      paymentData.razorpayAmount,
      currency:    "INR",
      name:        "Threadify",
      description: "Order #" + orderID,
      order_id:    paymentData.razorpayOrderId,
      handler: function(response) {
        fetch("/orders/payments/", {
          method:  "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
          body: JSON.stringify({
            orderID:              orderID,
            razorpay_payment_id:  response.razorpay_payment_id,
            razorpay_order_id:    response.razorpay_order_id,
            razorpay_signature:   response.razorpay_signature,
            payment_method:       "Razorpay",
          })
        }).then(r => {
          if (!r.ok) throw new Error('Payment verification failed: ' + r.status);
          return r.json();
        }).then(data => {
          if (data.order_number) {
            window.location.href = "/orders/order_complete/?order_number=" + data.order_number + "&payment_id=" + data.transID;
          } else {
            console.error("Invalid response:", data);
            alert("Payment verification error. Please try again.");
          }
        }).catch(err => {
          console.error("Payment Error:", err);
          alert("Error verifying payment: " + err.message);
        });
      },
      prefill: {
        name:    paymentData.userName || "",
        email:   paymentData.userEmail || "",
        contact: paymentData.userPhone || "",
      },
      theme: { color: "#C9A84C" }
    };

    const rzp = new Razorpay(rzpOptions);

    document.getElementById("pay-button").addEventListener("click", function(e) {
      e.preventDefault();
      rzp.open();
    });
  }
});
