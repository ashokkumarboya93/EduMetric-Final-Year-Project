// Landing Page JavaScript Functions

// Direct navigation to dashboard
function directToDashboard() {
    document.getElementById('landing-page').style.display = 'none';
    document.getElementById('app-shell').style.display = 'flex';
    
    // Initialize the dashboard
    if (typeof initializeDashboard === 'function') {
        initializeDashboard();
    }
}

// Direct navigation to specific mode
function directToMode(mode) {
    document.getElementById('landing-page').style.display = 'none';
    document.getElementById('app-shell').style.display = 'flex';
    
    // Initialize the dashboard and switch to specific mode
    if (typeof initializeDashboard === 'function') {
        initializeDashboard();
        setTimeout(() => {
            if (typeof switchMode === 'function') {
                switchMode(mode);
            }
        }, 100);
    }
}

// Back to landing page
function backToLanding() {
    document.getElementById('app-shell').style.display = 'none';
    document.getElementById('landing-page').style.display = 'flex';
}

// Scroll animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.scroll-animate').forEach(el => {
        observer.observe(el);
    });
}

// Initialize landing page
document.addEventListener('DOMContentLoaded', function() {
    // Show landing page by default
    document.getElementById('landing-page').style.display = 'flex';
    document.getElementById('app-shell').style.display = 'none';
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Add ripple effects
    document.querySelectorAll('.ripple-effect').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

// Profile dropdown toggle
function toggleProfile() {
    const menu = document.getElementById('profile-menu');
    menu.classList.toggle('show');
}

// Close profile dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.querySelector('.profile-dropdown');
    const menu = document.getElementById('profile-menu');
    
    if (dropdown && !dropdown.contains(event.target)) {
        menu.classList.remove('show');
    }
});