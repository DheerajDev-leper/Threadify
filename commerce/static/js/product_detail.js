/**
 * product_detail.js
 *
 * Handles the variant picker on the product detail page:
 *   - Auto-selects the cheapest size (and its color) on page load
 *   - Updates the displayed price live whenever size or color changes
 *   - Disables size pills that have no active variant for the chosen color
 *   - Shows an out-of-stock notice when the chosen combination has stock === 0
 *   - Writes the correct variant_id into the hidden form field before add-to-cart
 *   - Switches gallery images when a color is selected
 *
 * Called from the inline <script> at the bottom of product_detail.html:
 *   initializeProductDetail(defaultPrice, variantsJson, defaultSize, galleryByColor, defaultImageUrl)
 *
 * variantsJson shape (array):
 *   [{ id, color, size, price, stock }, ...]
 *
 * galleryByColor shape (object):
 *   { "Blue": ["url1", "url2"], "Gray": ["url3"], "": ["url4"] }
 *   Key "" = untagged images shown for every color.
 */

'use strict';

function initializeProductDetail(defaultPrice, variants, defaultSize, galleryByColor, defaultImageUrl) {

  /* ── DOM refs ────────────────────────────────────────────── */
  const priceEl      = document.getElementById('productPrice');
  const variantInput = document.getElementById('variantIdInput');
  const stockNotice  = document.getElementById('variantStockNotice');
  const addCartBtn   = document.getElementById('addCartBtn');
  const sizeLabel    = document.getElementById('sizeLabel');
  const colorLabel   = document.getElementById('colorLabel');

  /* ── State ───────────────────────────────────────────────── */
  let selectedSize  = null;
  let selectedColor = null;

  /* ── Price helpers ───────────────────────────────────────── */

  function formatPrice(amount) {
    return 'Rs' + Math.round(amount).toLocaleString('en-IN');
  }

  function findVariant(size, color) {
    if (!size) return null;
    if (color) {
      const exact = variants.find(v => v.size === size && v.color === color);
      if (exact) return exact;
    }
    const bySizeCandidates = variants.filter(v => v.size === size);
    if (!bySizeCandidates.length) return null;
    return bySizeCandidates.reduce(
      (best, v) => (v.price < best.price ? v : best),
      bySizeCandidates[0]
    );
  }

  function applyVariant(variant) {
    if (!variant) {
      if (priceEl) priceEl.textContent = formatPrice(defaultPrice);
      if (variantInput) variantInput.value = '';
      setStockNotice(null);
      return;
    }
    if (priceEl) {
      priceEl.classList.add('price-updating');
      priceEl.textContent = formatPrice(variant.price);
      setTimeout(() => priceEl.classList.remove('price-updating'), 300);
    }
    if (variantInput) variantInput.value = variant.id;
    setStockNotice(variant.stock);
  }

  function setStockNotice(stock) {
    if (!stockNotice) return;
    if (stock === null) {
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

  function refreshPillStates() {
    document.querySelectorAll('.size-pill').forEach(pill => {
      const size = pill.dataset.value;
      const available = selectedColor
        ? variants.some(v => v.size === size && v.color === selectedColor)
        : variants.some(v => v.size === size);
      pill.classList.toggle('unavailable', !available);
    });

    document.querySelectorAll('.color-swatch').forEach(swatch => {
      const color = swatch.dataset.value;
      const available = selectedSize
        ? variants.some(v => v.color === color && v.size === selectedSize)
        : variants.some(v => v.color === color);
      swatch.classList.toggle('unavailable', !available);
    });
  }

  /* ── Gallery switching ───────────────────────────────────── */

  /**
   * Attach click handlers to all .thumb-link elements.
   * Called once on init (for server-rendered thumbs) and again
   * after switchGallery rebuilds the thumbnail list.
   */
  function attachThumbHandlers() {
    document.querySelectorAll('.thumb-link').forEach(link => {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        const mainImg = document.getElementById('mainImg');
        if (mainImg) {
          mainImg.style.opacity = '0.5';
          mainImg.src = this.getAttribute('href');
          mainImg.onload = () => { mainImg.style.opacity = '1'; };
          // Fallback in case onload doesn't fire (cached image)
          setTimeout(() => { mainImg.style.opacity = '1'; }, 200);
        }
        document.querySelectorAll('.gallery-thumbs img').forEach(img => img.classList.remove('active'));
        this.querySelector('img').classList.add('active');
      });
    });
  }

  /**
   * Rebuild the main image and thumbnail strip for the given color.
   *
   * Image priority:
   *   1. Gallery images tagged to this color
   *   2. Gallery images with no color tag (shown for all colors)
   *   3. If nothing at all, fall back to product cover image
   */
  function switchGallery(color) {
    const mainImg    = document.getElementById('mainImg');
    const thumbsList = document.querySelector('.gallery-thumbs');
    if (!thumbsList || !galleryByColor) return;

    // Build ordered image list
    let images = [];

    if (color && galleryByColor[color] && galleryByColor[color].length) {
      images = images.concat(galleryByColor[color]);
    }

    // Untagged images always appear alongside any color
    if (galleryByColor[''] && galleryByColor[''].length) {
      images = images.concat(galleryByColor['']);
    }

    // If still empty (no gallery images at all), fall back to all gallery images
    if (images.length === 0) {
      Object.values(galleryByColor).forEach(urls => { images = images.concat(urls); });
    }

    // Fade-swap main image
    if (mainImg) {
      const nextSrc = images.length > 0 ? images[0] : defaultImageUrl;
      mainImg.style.transition = 'opacity 0.18s ease';
      mainImg.style.opacity = '0.4';
      setTimeout(() => {
        mainImg.src = nextSrc;
        mainImg.style.opacity = '1';
      }, 120);
    }

    // Rebuild thumbnail list
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

    // Re-attach click handlers now that the DOM has been rebuilt
    attachThumbHandlers();
  }

  /* ── Public selection handlers (called by onclick in template) ── */

  window.selectSize = function (el) {
    document.querySelectorAll('.size-pill').forEach(p => p.classList.remove('active'));
    el.classList.add('active');

    selectedSize = el.dataset.value;
    if (sizeLabel) sizeLabel.textContent = selectedSize;

    refreshPillStates();

    const variant = findVariant(selectedSize, selectedColor);
    if (selectedColor && !variant) clearColor();

    applyVariant(findVariant(selectedSize, selectedColor));
  };

  window.selectColor = function (el) {
    document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
    el.classList.add('active');

    selectedColor = el.dataset.value;
    if (colorLabel) colorLabel.textContent = selectedColor;

    refreshPillStates();
    applyVariant(findVariant(selectedSize, selectedColor));

    // ← Switch gallery images for this color
    switchGallery(selectedColor);
  };

  function clearColor() {
    selectedColor = null;
    document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
    if (colorLabel) colorLabel.textContent = '— select';
  }

  /* ── Attach handlers to server-rendered thumbnails on load ── */
  attachThumbHandlers();

  /* ── Auto-select on page load ────────────────────────────── */
  (function autoSelect() {
    if (!variants || !variants.length) return;

    let target = variants.find(v => v.size === defaultSize);
    if (!target) {
      target = variants.reduce((best, v) => (v.price < best.price ? v : best), variants[0]);
    }
    if (!target) return;

    const sizePill = document.querySelector(
      `.size-pill[data-value="${CSS.escape(target.size)}"]`
    );
    if (sizePill) sizePill.click();

    // Clicking the color swatch will automatically call switchGallery
    if (target.color) {
      const colorSwatch = document.querySelector(
        `.color-swatch[data-value="${CSS.escape(target.color)}"]`
      );
      if (colorSwatch) colorSwatch.click();
    }
  })();
}