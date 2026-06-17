var basePrice = 0;
var productVariants = [];
var hasColors = false;
var hasSizes = false;
var selectedColor = null;
var selectedSize = null;

function initializeProductDetail(productPrice, variants) {
  basePrice = productPrice;
  productVariants = variants || [];
  hasColors = productVariants.some(function (v) { return v.color; });
  hasSizes  = productVariants.some(function (v) { return v.size; });

  initThumbnailSwitcher();
  initFormValidation();

  if (productVariants.length) {
    if (!hasColors && !hasSizes) {
      // A single "default" variant with no colour/size axes — auto-select it
      // so the cart still records which combination (and therefore which
      // stock count) the shopper is buying.
      var input = document.getElementById('variantIdInput');
      if (input) input.value = productVariants[0].id;
    } else {
      applyAvailability();
      updateSelection();
    }
  }
}

function initThumbnailSwitcher() {
  document.querySelectorAll('.thumb-link').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      var src = this.getAttribute('href');
      var mainImg = document.getElementById('mainImg');
      if (mainImg) mainImg.src = src;
      document.querySelectorAll('.gallery-thumbs img').forEach(function (img) {
        img.classList.remove('active');
      });
      this.querySelector('img').classList.add('active');
    });
  });
}

function findVariant(color, size) {
  return productVariants.find(function (v) {
    return (v.color || '') === (color || '') && (v.size || '') === (size || '');
  });
}

function selectColor(el) {
  if (el.classList.contains('unavailable')) return;
  document.querySelectorAll('.color-swatch').forEach(function (s) { s.classList.remove('active'); });
  el.classList.add('active');
  selectedColor = el.dataset.value;
  var colorLabel = document.getElementById('colorLabel');
  if (colorLabel) colorLabel.textContent = selectedColor;
  applyAvailability();
  updateSelection();
}

function selectSize(el) {
  if (el.classList.contains('unavailable')) return;
  document.querySelectorAll('.size-pill').forEach(function (s) { s.classList.remove('active'); });
  el.classList.add('active');
  selectedSize = el.dataset.value;
  var sizeLabel = document.getElementById('sizeLabel');
  if (sizeLabel) sizeLabel.textContent = selectedSize;
  applyAvailability();
  updateSelection();
}

// Cross-disable: once one axis is picked, grey out options on the other
// axis that don't form an in-stock combination — the same behaviour as
// picking a colour on a marketplace listing and watching sizes update.
function applyAvailability() {
  if (hasSizes) {
    document.querySelectorAll('.size-pill').forEach(function (pill) {
      pill.classList.toggle('unavailable', !sizeIsAvailable(pill.dataset.value));
    });
  }
  if (hasColors) {
    document.querySelectorAll('.color-swatch').forEach(function (swatch) {
      swatch.classList.toggle('unavailable', !colorIsAvailable(swatch.dataset.value));
    });
  }
}

function sizeIsAvailable(size) {
  if (hasColors && selectedColor) {
    var v = findVariant(selectedColor, size);
    return !!(v && v.stock > 0);
  }
  return productVariants.some(function (v) { return (v.size || '') === size && v.stock > 0; });
}

function colorIsAvailable(color) {
  if (hasSizes && selectedSize) {
    var v = findVariant(color, selectedSize);
    return !!(v && v.stock > 0);
  }
  return productVariants.some(function (v) { return (v.color || '') === color && v.stock > 0; });
}

function updateSelection() {
  var ready = (!hasColors || selectedColor) && (!hasSizes || selectedSize);
  var variant = ready ? findVariant(selectedColor, selectedSize) : null;

  var priceEl = document.getElementById('productPrice');
  var notice  = document.getElementById('variantStockNotice');
  var input   = document.getElementById('variantIdInput');

  if (variant) {
    if (input)   input.value = variant.id;
    if (priceEl) priceEl.textContent = 'Rs' + variant.price.toFixed(2);
    if (notice) {
      if (variant.stock <= 0) {
        notice.textContent = 'This combination is out of stock.';
        notice.style.display = 'block';
      } else if (variant.stock <= 5) {
        notice.textContent = 'Only ' + variant.stock + ' left.';
        notice.style.display = 'block';
      } else {
        notice.style.display = 'none';
      }
    }
  } else {
    if (input)   input.value = '';
    if (priceEl) priceEl.textContent = 'Rs' + basePrice.toFixed(2);
    if (notice)  notice.style.display = 'none';
  }

  if (priceEl) {
    priceEl.classList.remove('price-changed');
    void priceEl.offsetWidth;
    priceEl.classList.add('price-changed');
  }

  updateAddButtonState(variant, ready);
}

function updateAddButtonState(variant, ready) {
  var btn = document.getElementById('addCartBtn');
  if (!btn) return;
  if (!hasColors && !hasSizes) {
    btn.disabled = false;
    return;
  }
  btn.disabled = !(ready && variant && variant.stock > 0);
}

function initFormValidation() {
  var form = document.getElementById('addCartForm');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    if (!hasColors && !hasSizes) return;

    if (hasColors && !selectedColor) {
      e.preventDefault();
      alert('Please select a colour.');
      return;
    }
    if (hasSizes && !selectedSize) {
      e.preventDefault();
      alert('Please select a size.');
      return;
    }
    var variant = findVariant(selectedColor, selectedSize);
    if (!variant || variant.stock <= 0) {
      e.preventDefault();
      alert('That combination is out of stock.');
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

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.color-swatch[data-color]').forEach(function (swatch) {
    var key = swatch.dataset.color.trim().toLowerCase();
    swatch.style.background = colorMap[key] || key;
  });
});