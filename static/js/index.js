document.addEventListener('DOMContentLoaded', () => {
    // Landing Page Elements
    const landingPage = document.getElementById('landing-page');
    const mainDashboard = document.getElementById('main-dashboard');
    const getStartedBtn = document.getElementById('get-started-btn');
    const getDemoBtn = document.getElementById('get-demo-btn');

    // --- Demo / Guest Mode Logic ---
    const urlParams = new URLSearchParams(window.location.search);
    const isDemoMode = urlParams.get('demo') === '1';
    const isLoggedIn = !!document.getElementById('user-profile-btn');

    if (isDemoMode && !isLoggedIn) {
        landingPage?.classList.add('hidden');
        mainDashboard?.classList.remove('hidden');
        document.body.classList.add('mobile-dashboard-active');
        document.getElementById('demo-badge')?.classList.remove('hidden');
    }

    // --- Hero Actions ---
    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', () => {
            if (mainDashboard?.classList.contains('hidden')) {
                mainDashboard.classList.remove('hidden');
            }
            const loginBtn = document.getElementById('login-trigger-btn');
            if (loginBtn) {
                loginBtn.click();
            }
        });
    }

    if (getDemoBtn) {
        getDemoBtn.onclick = () => {
            window.location.href = '/?demo=1';
            return false;
        };
    }

    // --- Scroll Reveal Animation ---
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal-item').forEach(item => {
        revealObserver.observe(item);
    });

    // --- Showcase Slider Logic ---
    const slides = document.querySelectorAll('.showcase-slide');
    const dots = document.querySelectorAll('.nav-dot');
    let currentSlide = 0;

    function showSlide(index) {
        slides.forEach(s => s.classList.remove('active'));
        dots.forEach(d => d.classList.remove('active'));
        slides[index].classList.add('active');
        dots[index].classList.add('active');
    }

    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            currentSlide = parseInt(dot.getAttribute('data-target'));
            showSlide(currentSlide);
        });
    });

    // Auto-advance slider
    setInterval(() => {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }, 6000);

    // --- Contact Form Handling ---
    const contactForm = document.getElementById('contact-form');
    const contactFormContainer = document.getElementById('contact-form-container');
    const contactSuccess = document.getElementById('contact-success');
    const resetContactBtn = document.getElementById('reset-contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (contactFormContainer) {
                contactFormContainer.style.opacity = '0';
                contactFormContainer.style.transform = 'translateY(-20px)';
                setTimeout(() => {
                    contactFormContainer.classList.add('hidden');
                    contactSuccess?.classList.remove('hidden');
                }, 500);
            }
        });
    }

    if (resetContactBtn) {
        resetContactBtn.addEventListener('click', () => {
            contactSuccess?.classList.add('hidden');
            if (contactFormContainer) {
                contactFormContainer.classList.remove('hidden');
                setTimeout(() => {
                    contactFormContainer.style.opacity = '1';
                    contactFormContainer.style.transform = 'translateY(0)';
                }, 10);
            }
            contactForm?.reset();
        });
    }
});
