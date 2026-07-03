/* ============================================
   FlexGym - Main JavaScript
   ============================================ */

// ===== 1. STICKY NAVBAR =====
// Jab user scroll kare to navbar ka style change hoga
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// ===== 2. MOBILE MENU TOGGLE =====
const hamburger = document.getElementById('hamburger');
const navMenu = document.getElementById('nav-menu');

if (hamburger) {
    hamburger.addEventListener('click', function() {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });
}

// Mobile menu mein kisi link par click karne par menu close ho jaaye
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function() {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    });
});

// ===== 3. BACK TO TOP BUTTON =====
const backToTop = document.getElementById('backToTop');

window.addEventListener('scroll', function() {
    if (window.scrollY > 300) {
        backToTop.classList.add('show');
    } else {
        backToTop.classList.remove('show');
    }
});

backToTop.addEventListener('click', function() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// ===== 4. SMOOTH SCROLLING =====
// Saare anchor links pe smooth scroll lagao
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const target = document.querySelector(targetId);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ===== 5. SCROLL REVEAL ANIMATION =====
// Elements ko scroll karne par animate karo
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
        }
    });
}, observerOptions);

// Sab cards aur sections pe reveal class lagao
document.querySelectorAll('.glass-card, .section-header, .feature-card, .service-card, .trainer-card, .pricing-card, .testimonial-card').forEach(el => {
    el.classList.add('reveal');
    observer.observe(el);
});

// ===== 6. FLASH MESSAGE AUTO-HIDE =====
// Flash messages 5 second baad automatically hide ho jaayein
setTimeout(function() {
    document.querySelectorAll('.flash-message').forEach(msg => {
        msg.style.opacity = '0';
        msg.style.transform = 'translateX(400px)';
        setTimeout(() => msg.remove(), 300);
    });
}, 5000);

// ===== 7. ACTIVE NAV LINK =====
// Current page ke hisaab se nav link ko active karo
const currentPage = window.location.pathname;
document.querySelectorAll('.nav-link').forEach(link => {
    const linkPage = link.getAttribute('href');
    if (linkPage === currentPage || (currentPage === '/' && linkPage === '/')) {
        link.classList.add('active');
    }
});

// ===== 8. FORM VALIDATION ENHANCEMENT =====
// Saare forms pe custom validation lagao
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        // Required fields check karo
        this.querySelectorAll('input[required], textarea[required], select[required]').forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.style.borderColor = '#e63946';
                
                // Error message show karo
                let errorMsg = field.parentNode.querySelector('.field-error');
                if (!errorMsg) {
                    errorMsg = document.createElement('span');
                    errorMsg.className = 'field-error';
                    errorMsg.style.color = '#e63946';
                    errorMsg.style.fontSize = '12px';
                    errorMsg.style.marginTop = '5px';
                    errorMsg.textContent = 'Ye field zaroori hai';
                    field.parentNode.appendChild(errorMsg);
                }
            } else {
                field.style.borderColor = '';
                let errorMsg = field.parentNode.querySelector('.field-error');
                if (errorMsg) errorMsg.remove();
            }
        });
        
        // Email validation
        const emailField = this.querySelector('input[type="email"]');
        if (emailField && emailField.value) {
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(emailField.value)) {
                isValid = false;
                emailField.style.borderColor = '#e63946';
            }
        }
        
        if (!isValid) {
            e.preventDefault();
        }
    });
});

// ===== 9. NUMBER COUNTER ANIMATION =====
// Stats numbers ko animate karo
const animateCounter = (element, target, duration = 2000) => {
    const start = 0;
    const startTime = performance.now();
    
    const updateCounter = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(progress * target);
        
        // Agar "10K+" jaisa format hai to handle karo
        const suffix = element.textContent.replace(/[0-9]/g, '');
        element.textContent = current + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    };
    
    requestAnimationFrame(updateCounter);
};

// Jab stats section visible ho tab counter start karo
const statsObserver = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = entry.target.querySelectorAll('.stat-number, .stat-box h3');
            statNumbers.forEach(num => {
                const text = num.textContent;
                const numericValue = parseInt(text.replace(/[^0-9]/g, ''));
                if (numericValue && !num.dataset.animated) {
                    num.dataset.animated = 'true';
                    animateCounter(num, numericValue);
                }
            });
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.hero-stats, .stats-grid').forEach(el => {
    statsObserver.observe(el);
});

// ===== 10. CLOSE MOBILE MENU ON OUTSIDE CLICK =====
document.addEventListener('click', function(e) {
    if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    }
});

// ===== 11. KEYBOARD ACCESSIBILITY =====
// Escape key se mobile menu close karo
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
        
        // Image modal bhi close karo
        const modal = document.getElementById('imageModal');
        if (modal) modal.style.display = 'none';
    }
});

console.log('💪 FlexGym Website Loaded Successfully!');