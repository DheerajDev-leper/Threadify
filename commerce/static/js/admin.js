/* ============================================================
   StyleAdmin — admin.js
   ============================================================ */

(function () {
  'use strict';

  /* ── Sidebar toggle (mobile) ─────────────────────────────── */
  const sidebar       = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');

  if (sidebar && sidebarToggle) {
    // Open / close on button click
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });

    // Close when clicking the overlay (the box-shadow backdrop)
    document.addEventListener('click', function (e) {
      if (
        sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        e.target !== sidebarToggle
      ) {
        sidebar.classList.remove('open');
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        sidebarToggle.focus();
      }
    });
  }

  /* ── Auto-dismiss alerts after 5 s ──────────────────────── */
  function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
      setTimeout(function () {
        alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        alert.style.opacity    = '0';
        alert.style.transform  = 'translateY(-6px)';
        setTimeout(function () {
          alert.remove();
        }, 420);
      }, 5000);
    });
  }

  /* ── Init ────────────────────────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoDismissAlerts);
  } else {
    autoDismissAlerts();
  }
})();