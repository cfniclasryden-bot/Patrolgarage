/* ============================================
   PATROL GARAGE DUBAI - JavaScript
   Mobile menu, smooth scroll, form handling
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
  initMobileMenu();
  initSmoothScroll();
  initFormHandling();
});

/**
 * Mobile menu toggle
 */
function initMobileMenu() {
  const menuToggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('nav');

  if (menuToggle) {
    menuToggle.addEventListener('click', function() {
      nav.classList.toggle('open');
    });

    // Close menu when clicking a link
    const navLinks = nav.querySelectorAll('a');
    navLinks.forEach(link => {
      link.addEventListener('click', function() {
        nav.classList.remove('open');
      });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
      if (!e.target.closest('header')) {
        nav.classList.remove('open');
      }
    });
  }
}

/**
 * Smooth scroll for anchor links
 */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;

      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
}

/**
 * Form handling for Netlify
 */
function initFormHandling() {
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      // Netlify will handle the form submission
      // This is just for any client-side validation if needed
    });
  });
}

/**
 * Lazy load images (using native loading="lazy")
 * This is handled by the HTML, but we can enhance it if needed
 */
