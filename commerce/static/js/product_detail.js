'use strict';

function initializeProductDetail(defaultPrice, variants, defaultSize, galleryByColor, defaultImageUrl) {

  /* ── DOM refs ────────────────────────────────────────────── */
  const priceEl      = document.getElementById('productPrice');
  const variantInput = document.getElementById('variantIdInput');
  const stockNotice  = document.getElementById('variantStockNotice');
  const addCartBtn   = document.getElementById('addCartBtn');
  const comboWrap    = document.getElementById('variantCombos');

  /* ── State ───────────────────────────────────────────────── */
  let selectedVariantId = null;

  /* ── Helpers ─────────────────────────────────────────────── */

  function formatPrice(amount) {
    return 'Rs' + Math.round(amount).toLocaleString('en-IN');
  }

  function setStockNotice(stock) {
    if (!stockNotice) return;
    if (stock === null || stock === undefined) {
      stockNotice.style.display = 'none';
      if (addCartBtn) addCartBtn.disabled = false;
      return;
    }
    if (stock === 0) {
      stockNotice.style.display = 'block';
      stockNotice.className = 'variant-stock-notice out-of-stock';
      stockNotice.innerHTML = '<i class="fa fa-times-circle"></i> Out of stock for this option';
      if (addCartBtn) addCartBtn.disabled = true;
    } else if (stock <= 5) {
      stockNotice.style.display = 'block';
      stockNotice.className = 'variant-stock-notice low-stock';
      stockNotice.innerHTML = '<i class="fa fa-exclamation-circle"></i> Only ' + stock + ' left — order soon';
      if (addCartBtn) addCartBtn.disabled = false;
    } else {
      stockNotice.style.display = 'none';
      if (addCartBtn) addCartBtn.disabled = false;
    }
  }

  /* ── Build combo cards ───────────────────────────────────── */

  const COLOR_MAP = {
    'black':      '#1c1c1c',
    'white':      '#f5f5f5',
    'grey':       '#9ca3af',
    'gray':       '#9ca3af',
    'navy blue':  '#1e3a5f',
    'navy':       '#1e3a5f',
    'blue':       '#2563eb',
    'red':        '#dc2626',
    'maroon':     '#7f1d1d',
    'pink':       '#ec4899',
    'purple':     '#7c3aed',
    'green':      '#16a34a',
    'olive':      '#5c6b2f',
    'yellow':     '#facc15',
    'mustard':    '#d4a017',
    'orange':     '#f97316',
    'brown':      '#78350f',
    'beige':      '#d8c4a0',
    'khaki':      '#bdb76b',
    'multicolor': 'linear-gradient(135deg,#ef4444,#facc15,#22c55e,#3b82f6)',
    'multi':      'linear-gradient(135deg,#ef4444,#facc15,#22c55e,#3b82f6)',
  };

  function buildCombos() {
    if (!comboWrap || !variants || !variants.length) return;

    comboWrap.innerHTML = '';

    variants.forEach(v => {
      const card = document.createElement('div');
      card.className = 'variant-combo-card';
      card.dataset.variantId = v.id;
      card.dataset.color     = v.color;
      card.dataset.size      = v.size;

      if (v.stock === 0) card.classList.add('out-of-stock');

      // Colour dot
      const dot = document.createElement('span');
      dot.className = 'combo-color-dot';
      const bg = COLOR_MAP[(v.color || '').toLowerCase().trim()];
      if (bg) dot.style.background = bg;

      // Label  "Navy Blue · L"
      const label = document.createElement('span');
      label.className = 'combo-label';
      const parts = [];
      if (v.color) parts.push(v.color);
      if (v.size)  parts.push(v.size);
      label.textContent = parts.join(' · ');

      // Price
      const price = document.createElement('span');
      price.className = 'combo-price';
      price.textContent = formatPrice(v.price);

      card.appendChild(dot);
      card.appendChild(label);
      card.appendChild(price);

      if (v.stock === 0) {
        const oos = document.createElement('span');
        oos.className = 'combo-oos-badge';
        oos.textContent = 'Out of stock';
        card.appendChild(oos);
      }

      card.addEventListener('click', () => {
        if (v.stock === 0) return;
        selectVariantCard(card, v);
      });

      comboWrap.appendChild(card);
    });
  }

  function selectVariantCard(card, v) {
    document.querySelectorAll('.variant-combo-card').forEach(c => c.classList.remove('active'));
    card.classList.add('active');

    selectedVariantId = v.id;
    if (variantInput) variantInput.value = v.id;

    if (priceEl) {
      priceEl.classList.add('price-updating');
      priceEl.textContent = formatPrice(v.price);
      setTimeout(() => priceEl.classList.remove('price-updating'), 300);
    }

    setStockNotice(v.stock);
    switchGallery(v.color);
  }

  /* ── Gallery switching ───────────────────────────────────── */

  function attachThumbHandlers() {
    document.querySelectorAll('.thumb-link').forEach(link => {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        const mainImg = document.getElementById('mainImg');
        if (mainImg) {
          mainImg.style.opacity = '0.5';
          mainImg.src = this.getAttribute('href');
          mainImg.onload = () => { mainImg.style.opacity = '1'; };
          setTimeout(() => { mainImg.style.opacity = '1'; }, 200);
        }
        document.querySelectorAll('.gallery-thumbs img').forEach(img => img.classList.remove('active'));
        this.querySelector('img').classList.add('active');
      });
    });
  }

  function switchGallery(color) {
    const mainImg    = document.getElementById('mainImg');
    const thumbsList = document.querySelector('.gallery-thumbs');
    if (!thumbsList || !galleryByColor) return;

    let images = [];
    if (color && galleryByColor[color] && galleryByColor[color].length) {
      images = images.concat(galleryByColor[color]);
    }
    if (galleryByColor[''] && galleryByColor[''].length) {
      images = images.concat(galleryByColor['']);
    }
    if (images.length === 0) {
      Object.values(galleryByColor).forEach(urls => { images = images.concat(urls); });
    }

    if (mainImg) {
      const nextSrc = images.length > 0 ? images[0] : defaultImageUrl;
      mainImg.style.transition = 'opacity 0.18s ease';
      mainImg.style.opacity = '0.4';
      setTimeout(() => {
        mainImg.src = nextSrc;
        mainImg.style.opacity = '1';
      }, 120);
    }

    thumbsList.innerHTML = '';
    const thumbImages = images.length > 0 ? images : [defaultImageUrl];
    thumbImages.forEach((url, i) => {
      const li  = document.createElement('li');
      const a   = document.createElement('a');
      a.href    = url;
      a.className = 'thumb-link';
      const img = document.createElement('img');
      img.src   = url;
      img.alt   = 'Product image ' + (i + 1);
      if (i === 0) img.classList.add('active');
      a.appendChild(img);
      li.appendChild(a);
      thumbsList.appendChild(li);
    });

    attachThumbHandlers();
  }

  /* ── Init ────────────────────────────────────────────────── */

  attachThumbHandlers();
  buildCombos();

  // Auto-select cheapest in-stock variant (prefer defaultSize)
  (function autoSelect() {
    if (!variants || !variants.length) return;

    let target = variants.find(v => v.size === defaultSize && v.stock > 0);
    if (!target) {
      target = variants
        .filter(v => v.stock > 0)
        .reduce((best, v) => (!best || v.price < best.price ? v : best), null);
    }
    if (!target) target = variants[0]; // fallback: first variant even if OOS

    const card = comboWrap
      ? comboWrap.querySelector(`.variant-combo-card[data-variant-id="${target.id}"]`)
      : null;

    if (card) selectVariantCard(card, target);
  })();
}