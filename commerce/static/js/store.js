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
