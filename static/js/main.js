// ClassAlert - Enhanced JavaScript functionality

// Utility Functions
const ClassAlert = {
  // Show toast notification
  showToast: function(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-icon">
        <i class="ri-${this.getToastIcon(type)}-line"></i>
      </div>
      <div class="toast-message">${message}</div>
      <button class="toast-close" onclick="this.parentElement.remove()">
        <i class="ri-close-line"></i>
      </button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  },

  getToastIcon: function(type) {
    const icons = {
      success: 'checkbox-circle',
      error: 'error-warning',
      warning: 'alert',
      info: 'information'
    };
    return icons[type] || icons.info;
  },

  // Form validation
  validateForm: function(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    const inputs = form.querySelectorAll('input[required], textarea[required]');
    let isValid = true;

    inputs.forEach(input => {
      if (!input.value.trim()) {
        input.classList.add('error');
        isValid = false;
      } else {
        input.classList.remove('error');
      }
    });

    return isValid;
  },

  // Confirm action
  confirmAction: function(message) {
    return confirm(message);
  },

  // Local storage helper
  storage: {
    set: function(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
      } catch (e) {
        console.error('Error saving to localStorage:', e);
        return false;
      }
    },
    
    get: function(key) {
      try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
      } catch (e) {
        console.error('Error reading from localStorage:', e);
        return null;
      }
    },
    
    remove: function(key) {
      try {
        localStorage.removeItem(key);
        return true;
      } catch (e) {
        console.error('Error removing from localStorage:', e);
        return false;
      }
    }
  }
};

// Enhanced form handling
document.addEventListener('DOMContentLoaded', function() {
  // Add smooth scroll to all anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Add loading state to all forms
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
      const submitBtn = this.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="ri-loader-4-line"></i> Loading...';
        submitBtn.style.animation = 'spin 1s linear infinite';
      }
    });
  });

  // Add fade-in animation to cards
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.card, .tile, .form-container').forEach(el => {
    observer.observe(el);
  });

  // Auto-hide alerts after 5 seconds
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.animation = 'fadeOut 0.5s ease-out';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
});

// Request notification permission
if ('Notification' in window && Notification.permission === 'default') {
  setTimeout(() => {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        ClassAlert.showToast('Notifications enabled! You will receive class alerts.', 'success');
      }
    });
  }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes fadeOut {
    from {
      opacity: 1;
    }
    to {
      opacity: 0;
    }
  }

  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .fade-in {
    animation: fadeIn 0.6s ease-out;
  }

  .toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: white;
    padding: 16px 20px;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 300px;
    z-index: 10000;
    animation: slideIn 0.3s ease-out;
    border-left: 4px solid #5b4bff;
  }

  .toast-success { border-left-color: #28a745; }
  .toast-error { border-left-color: #dc3545; }
  .toast-warning { border-left-color: #ffc107; }
  .toast-info { border-left-color: #17a2b8; }

  .toast-icon {
    font-size: 24px;
    color: #5b4bff;
  }

  .toast-success .toast-icon { color: #28a745; }
  .toast-error .toast-icon { color: #dc3545; }
  .toast-warning .toast-icon { color: #ffc107; }
  .toast-info .toast-icon { color: #17a2b8; }

  .toast-message {
    flex: 1;
    font-weight: 500;
  }

  .toast-close {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    color: #999;
    font-size: 18px;
  }

  .toast-close:hover {
    color: #333;
  }

  input.error,
  textarea.error {
    border-color: #dc3545 !important;
    box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1) !important;
  }
`;
document.head.appendChild(style);

// Export for global use
window.ClassAlert = ClassAlert;

