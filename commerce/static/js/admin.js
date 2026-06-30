

'use strict';

/* ── Password visibility toggle ─────────────────────────── */

/**
 * Wire up a show/hide toggle button for a password field.
 * @param {string} btnId   - id of the <button>
 * @param {string} fieldId - id of the <input type="password">
 * @param {string} showId  - id of the "eye open" SVG
 * @param {string} hideId  - id of the "eye closed" SVG
 */
function makePasswordToggle(btnId, fieldId, showId, hideId) {
  var btn   = document.getElementById(btnId);
  var field = document.getElementById(fieldId);
  var show  = document.getElementById(showId);
  var hide  = document.getElementById(hideId);
  if (!btn || !field) return;
  btn.addEventListener('click', function () {
    var isPass = field.type === 'password';
    field.type = isPass ? 'text' : 'password';
    if (show) show.style.display = isPass ? 'none'  : 'block';
    if (hide) hide.style.display = isPass ? 'block' : 'none';
    btn.setAttribute('aria-label', isPass ? 'Hide password' : 'Show password');
  });
}

/* Simple one-SVG variant (shop_register inline buttons) */
function togglePw(id) {
  var input = document.getElementById(id);
  if (input) input.type = input.type === 'password' ? 'text' : 'password';
}

/* ── Form loading state ──────────────────────────────────── */

/**
 * Adds a .loading class to a button when its form submits.
 * @param {string} formId
 * @param {string} btnId
 */
function addFormLoadingState(formId, btnId) {
  var form = document.getElementById(formId);
  var btn  = document.getElementById(btnId);
  if (!form || !btn) return;
  form.addEventListener('submit', function () {
    btn.classList.add('loading');
    btn.disabled = true;
  });
}

/* ── Password strength meter (single bar, shop_register) ── */

var STRENGTH_LEVELS = [
  { pct: '0%',   color: '',        text: 'Enter a password' },
  { pct: '25%',  color: '#ef4444', text: 'Too weak' },
  { pct: '50%',  color: '#f97316', text: 'Fair' },
  { pct: '75%',  color: '#eab308', text: 'Good' },
  { pct: '100%', color: '#22c55e', text: 'Strong' },
];

function checkStrength(pw) {
  var bar   = document.getElementById('pwBar');
  var label = document.getElementById('pwLabel');
  if (!bar || !label) return;

  var score = 0;
  if (pw.length >= 8)             score++;
  if (pw.length >= 12)            score++;
  if (/[A-Z]/.test(pw))          score++;
  if (/[0-9]/.test(pw))          score++;
  if (/[^A-Za-z0-9]/.test(pw))   score++;

  var lvl = STRENGTH_LEVELS[Math.min(score, 4)];
  bar.style.width      = lvl.pct;
  bar.style.background = lvl.color;
  label.textContent    = lvl.text;
  label.style.color    = lvl.color || '#4e5668';
}

/* ── Segmented strength bar + match check (reset_password) ─ */

var SEG_LEVELS = [
  { color: '#ef4444', label: 'Too short' },
  { color: '#f97316', label: 'Weak' },
  { color: '#eab308', label: 'Fair' },
  { color: '#22c55e', label: 'Strong' },
];

function calcStrength(pw) {
  if (pw.length < 6) return 0;
  var score = 1;
  if (pw.length >= 10) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw) && /[^a-zA-Z0-9]/.test(pw)) score++;
  return Math.min(score, 4);
}

function initResetPasswordPage() {
  var pw1           = document.getElementById('id_password1');
  var pw2           = document.getElementById('id_password2');
  var segs          = [1, 2, 3, 4].map(function (i) { return document.getElementById('seg' + i); });
  var strengthLabel = document.getElementById('strengthLabel');
  var matchLabel    = document.getElementById('matchLabel');

  if (!pw1 || !pw2) return;

  function checkMatch() {
    if (!pw2.value) { if (matchLabel) matchLabel.textContent = ''; return; }
    if (pw1.value === pw2.value) {
      matchLabel.textContent = 'Passwords match ✓';
      matchLabel.style.color = '#22c55e';
    } else {
      matchLabel.textContent = 'Passwords do not match';
      matchLabel.style.color = '#f87171';
    }
  }

  pw1.addEventListener('input', function () {
    var s = calcStrength(pw1.value);
    segs.forEach(function (seg, i) {
      if (seg) seg.style.background = i < s ? SEG_LEVELS[s - 1].color : 'rgba(255,255,255,0.08)';
    });
    if (strengthLabel) {
      strengthLabel.textContent = pw1.value.length ? SEG_LEVELS[Math.max(s - 1, 0)].label : '';
      strengthLabel.style.color = s > 0 ? SEG_LEVELS[s - 1].color : 'var(--text-muted)';
    }
    checkMatch();
  });

  pw2.addEventListener('input', checkMatch);

  makePasswordToggle('togglePw1', 'id_password1', 'eye1Show', 'eye1Hide');
  makePasswordToggle('togglePw2', 'id_password2', 'eye2Show', 'eye2Hide');
}

/* ── Shop-register form validation ──────────────────────── */

function initShopRegisterPage() {
  var regForm = document.getElementById('regForm');
  var regBtn  = document.getElementById('regBtn');

  if (!regForm || !regBtn) return;

  regForm.addEventListener('submit', function (e) {
    var pw1   = document.getElementById('pw1');
    var pw2   = document.getElementById('pw2');
    var terms = document.querySelector('[name="terms"]');

    if (pw1 && pw2 && pw1.value !== pw2.value) {
      e.preventDefault();
      alert('Passwords do not match.');
      return;
    }
    if (terms && !terms.checked) {
      e.preventDefault();
      alert('Please agree to the terms of service.');
      return;
    }
    regBtn.classList.add('loading');
    regBtn.disabled = true;
  });
}

/* ── Login page ──────────────────────────────────────────── */

function initLoginPage() {
  /* Password toggle */
  makePasswordToggle('togglePassword', 'id_password', 'eyeShow', 'eyeHide');

  /* Form loading */
  var form     = document.getElementById('loginForm');
  var loginBtn = document.getElementById('loginBtn');
  if (form && loginBtn) {
    form.addEventListener('submit', function () {
      loginBtn.classList.add('loading');
      loginBtn.disabled = true;
    });
  }

  /* Highlight field errors */
  document.querySelectorAll('.field-error').forEach(function (input) {
    input.style.borderColor = 'rgba(239,68,68,0.5)';
    input.style.boxShadow   = '0 0 0 3px rgba(239,68,68,0.1)';
  });
}