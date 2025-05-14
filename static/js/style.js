document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const createMobileNav = () => {
        const header = document.querySelector('header');
        if (!header) return;

        if (!document.querySelector('.mobile-menu-btn')) {
            const mobileBtn = document.createElement('button');
            mobileBtn.classList.add('mobile-menu-btn');
            mobileBtn.innerHTML = '<i class="fas fa-bars"></i>';
            header.appendChild(mobileBtn);

            mobileBtn.addEventListener('click', function() {
                const nav = header.querySelector('nav');
                nav.classList.toggle('show');
                this.innerHTML = nav.classList.contains('show') 
                    ? '<i class="fas fa-times"></i>' 
                    : '<i class="fas fa-bars"></i>';
            });
        }
    };

    const checkMobile = () => {
        if (window.innerWidth <= 768) {
            createMobileNav();
            document.body.classList.add('mobile');
        } else {
            document.body.classList.remove('mobile');
            const nav = document.querySelector('nav');
            if (nav) nav.classList.remove('show');
        }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);

    // Animate elements on scroll
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.card, .form-container');
        
        const isInViewport = (el) => {
            const rect = el.getBoundingClientRect();
            return (
                rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.bottom >= 0
            );
        };

        elements.forEach(element => {
            if (isInViewport(element) && !element.classList.contains('animated')) {
                element.classList.add('animated');
            }
        });
    };

    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll();

    // Notification badge animation
    const notifications = document.querySelectorAll('.notification-badge');
    notifications.forEach(badge => {
        badge.addEventListener('click', function() {
            this.classList.add('pulse');
            setTimeout(() => this.classList.remove('pulse'), 300);
        });
    });

    // Timestamp hover behavior
    const timestamps = document.querySelectorAll('.card-date');
    timestamps.forEach(timestamp => {
        const originalText = timestamp.textContent;
        timestamp.addEventListener('mouseenter', function() {
            const date = new Date(this.getAttribute('data-timestamp') || Date.parse(originalText));
            if (!isNaN(date.getTime())) {
                this.textContent = date.toLocaleString('fr-FR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        });
        timestamp.addEventListener('mouseleave', function() {
            this.textContent = originalText;
        });
    });

    // Category filter highlighting
    const highlightCategory = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const category = urlParams.get('categorie');
        
        if (category) {
            const categoryTags = document.querySelectorAll('.category-tag');
            categoryTags.forEach(tag => {
                if (tag.textContent.trim().toLowerCase().includes(category.toLowerCase())) {
                    tag.classList.add('highlighted');
                }
            });
        }
    };

    highlightCategory();

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Form validation (exclure les formulaires de vote)
    const validateForm = (form) => {
        if (form.classList.contains('vote-form')) return true; // Ignorer la validation pour les votes
        let isValid = true;
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('error');
                
                let errorMsg = input.parentNode.querySelector('.error-message');
                if (!errorMsg) {
                    errorMsg = document.createElement('div');
                    errorMsg.classList.add('error-message');
                    errorMsg.textContent = 'Ce champ est requis';
                    errorMsg.style.color = 'var(--danger)';
                    errorMsg.style.fontSize = '0.9rem';
                    errorMsg.style.marginTop = '0.25rem';
                    input.parentNode.appendChild(errorMsg);
                }
            } else {
                input.classList.remove('error');
                const errorMsg = input.parentNode.querySelector('.error-message');
                if (errorMsg) errorMsg.remove();
            }
        });
        
        return isValid;
    };

    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this) && !this.classList.contains('search-form') && !this.classList.contains('vote-form')) {
                e.preventDefault();
            }
        });
    });
});