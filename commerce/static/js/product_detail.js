var basePrice = 0;

function initializeProductDetail(productPrice) {
  basePrice = productPrice;
  initThumbnailSwitcher();
  initColorSwatches();
  initSizePills();
  initFormValidation();
}

function initThumbnailSwitcher() {
  document.querySelectorAll('.thumb-link').forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      var src = this.getAttribute('href');
      document.getElementById('mainImg').src = src;
      document.querySelectorAll('.gallery-thumbs img').forEach(function(img){
        img.classList.remove('active');
      });
      this.querySelector('img').classList.add('active');
    });
  });
}

function selectColor(el) {
  document.querySelectorAll('.color-swatch').forEach(function(s){ s.classList.remove('active'); });
  el.classList.add('active');
  document.getElementById('colorInput').value = el.dataset.value;
  document.getElementById('colorLabel').textContent = el.dataset.value;
  updatePrice();
}

function selectSize(el) {
  if (el.classList.contains('unavailable')) return;
  document.querySelectorAll('.size-pill').forEach(function(s){ s.classList.remove('active'); });
  el.classList.add('active');
  document.getElementById('sizeInput').value = el.dataset.value;
  document.getElementById('sizeLabel').textContent = el.dataset.value;
  updatePrice();
}

function updatePrice() {
  var colorEl = document.querySelector('.color-swatch.active');
  var sizeEl  = document.querySelector('.size-pill.active');
  var price   = basePrice;

  if (colorEl && parseFloat(colorEl.dataset.price) > 0) {
    price = parseFloat(colorEl.dataset.price);
  }
  if (sizeEl && parseFloat(sizeEl.dataset.price) > 0) {
    price = parseFloat(sizeEl.dataset.price);
  }

  var priceEl = document.getElementById('productPrice');
  priceEl.textContent = 'Rs' + price.toFixed(2);
  priceEl.classList.remove('price-changed');
  void priceEl.offsetWidth;
  priceEl.classList.add('price-changed');
}

function initColorSwatches() {
  // Color swatch selection is handled by selectColor function
}

function initSizePills() {
  // Size pill selection is handled by selectSize function
}

function initFormValidation() {
  var form = document.getElementById('addCartForm');
  if (!form) return;

  form.addEventListener('submit', function(e) {
    var colorPills = document.querySelectorAll('.color-swatch');
    var sizePills  = document.querySelectorAll('.size-pill');

    if (colorPills.length > 0 && !document.getElementById('colorInput').value) {
      e.preventDefault();
      alert('Please select a colour.');
      return;
    }
    if (sizePills.length > 0 && !document.getElementById('sizeInput').value) {
      e.preventDefault();
      alert('Please select a size.');
      return;
    }
  });
}
