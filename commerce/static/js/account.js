document.addEventListener('DOMContentLoaded', function() {
  var pwInput = document.getElementById('newPwInput');
  if (!pwInput) return;

  pwInput.addEventListener('input', function() {
    var v = this.value, bar = document.getElementById('pwStrengthBar');
    var strength = 0;
    if (v.length >= 8) strength += 33;
    if (/[A-Z]/.test(v) && /[a-z]/.test(v)) strength += 33;
    if (/[0-9]/.test(v) || /[^a-zA-Z0-9]/.test(v)) strength += 34;
    bar.style.width = strength + '%';
    bar.style.background = strength < 40 ? '#8b2e2e' : strength < 75 ? 'var(--gold)' : '#4a7a40';
  });
});
