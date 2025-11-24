/**
 * Jukebox - Mobile UX JavaScript
 * Progressive enhancements for forms, toasts, and interactions
 */

// Toast notification system
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = {
    success: '✓',
    error: '✕',
    danger: '⚠',
    info: 'ℹ'
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  // Auto-dismiss after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Display flash messages on page load
document.addEventListener('DOMContentLoaded', () => {
  if (window.flashMessages) {
    window.flashMessages.forEach(msg => {
      showToast(msg.message, msg.type);
    });
  }
});

// Form submission loading states
document.addEventListener('DOMContentLoaded', () => {
  const forms = document.querySelectorAll('form[method="POST"]');

  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
      }
    });
  });
});

// Export for use in other scripts
window.showToast = showToast;
