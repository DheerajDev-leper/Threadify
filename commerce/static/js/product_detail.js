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
const colorMap = {
  'black':      '#1a1a1a',
  'white':      '#f5f5f5',
  'navy':       '#1b2a4a',
  'navy blue':  '#1b2a4a',
  'blue':       '#2d6aad',
  'red':        '#c0392b',
  'green':      '#2e7d4f',
  'brown':      '#6b3f2a',
  'gold':       '#c9a84c',
  'grey':       '#8a8a8a',
  'gray':       '#8a8a8a',
  'pink':       '#e8a0b0',
  'purple':     '#6b4fa0',
  'orange':     '#d4622a',
  'yellow':     '#d4a017',
  'cream':      '#faf8f4',
  'beige':      '#d9c9a8',
  'maroon':     '#6b1a1a',
  'teal':       '#1d9e75',
  'olive':      '#6b7a2a',
};

function selectColor(el) {
// Apply color backgrounds from map
  document.querySelectorAll('.color-swatch[data-color]').forEach(function(swatch) {
    const key = swatch.dataset.color.trim().toLowerCase();
    const hex = colorMap[key];
    if (hex) {
      swatch.style.background = hex;
    } else {
      // fallback: try using the value directly as CSS color
      swatch.style.background = key;
    }
  });
  el.classList.add('active');
  const val = el.dataset.value;
  document.getElementById('colorInput').value = val;
  // Show selected color name in label
  document.getElementById('colorLabel').textContent = val.charAt(0).toUpperCase() + val.slice(1);
  // Update price if variant has its own price
  const price = el.dataset.price;
  if (price) updatePrice(price);
}