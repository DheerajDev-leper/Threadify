function toggleFilters() {
  var drawer = document.getElementById('filterDrawer');
  var btn    = document.getElementById('filterToggle');
  drawer.classList.toggle('open');
  btn.classList.toggle('active');
}

window.addEventListener('DOMContentLoaded', function() {
  var params = new URLSearchParams(window.location.search);
  if (params.has('size') || params.has('color') ||
      params.has('min_price') || params.has('max_price')) {
    document.getElementById('filterDrawer').classList.add('open');
    document.getElementById('filterToggle').classList.add('active');
    buildActiveTags();
  }
});

function toggleSizeFilter(el) {
  el.classList.toggle('active');
  rebuildHiddenInputs('sizePillsFilter', 'sizeInputs', 'size');
}

function toggleColorFilter(el) {
  el.classList.toggle('active');
  rebuildHiddenInputs('colorDotsFilter', 'colorInputs', 'color');
}

function rebuildHiddenInputs(containerId, inputsId, name) {
  var container  = document.getElementById(containerId);
  var inputsWrap = document.getElementById(inputsId);
  var active     = container.querySelectorAll('.active');
  inputsWrap.innerHTML = '';
  active.forEach(function(el) {
    var input = document.createElement('input');
    input.type  = 'hidden';
    input.name  = name;
    input.value = el.dataset.value;
    inputsWrap.appendChild(input);
  });
  buildActiveTags();
}

function buildActiveTags() {
  var wrap   = document.getElementById('activeFilters');
  wrap.innerHTML = '';
  var params = new URLSearchParams(window.location.search);
  params.getAll('size').forEach(function(v) { addTag(wrap, 'Size: ' + v, 'size', v); });
  params.getAll('color').forEach(function(v){ addTag(wrap, 'Color: ' + v,'color',v); });
  if (params.get('min_price')) addTag(wrap, 'Min Rs'+params.get('min_price'), 'min_price', null);
  if (params.get('max_price')) addTag(wrap, 'Max Rs'+params.get('max_price'), 'max_price', null);
}

function addTag(wrap, label, key, val) {
  var tag = document.createElement('span');
  tag.className = 'active-filter-tag';
  tag.innerHTML = label + '<button type="button" onclick="removeFilter(\''+key+'\',\''+val+'\')">×</button>';
  wrap.appendChild(tag);
}

function removeFilter(key, val) {
  var params = new URLSearchParams(window.location.search);
  if (val) {
    var all = params.getAll(key).filter(function(v){ return v !== val; });
    params.delete(key);
    all.forEach(function(v){ params.append(key, v); });
  } else {
    params.delete(key);
  }
  window.location.search = params.toString();
}

(function applyFilterDotColors() {
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

  document.querySelectorAll('.filter-color-dot').forEach(dot => {
    const name = (dot.dataset.value || '').toLowerCase().trim();
    const bg   = COLOR_MAP[name];
    if (bg) dot.style.background = bg;
  });
})();