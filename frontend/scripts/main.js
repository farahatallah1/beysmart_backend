// Main application logic and UI management

class AppManager {
    constructor() {
        this.currentScreen = 'landing-screen';
        this.init();
    }

    init() {
        this.bindNavigationEvents();
        this.bindUIEvents();
        this.initializeApp();
    }

    bindNavigationEvents() {
        // Mobile navigation toggle
        const navToggle = document.getElementById('nav-toggle');
        const navMenu = document.getElementById('nav-menu');
        
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navToggle.classList.toggle('active');
                navMenu.classList.toggle('active');
            });

            // Close mobile menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                    navToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            });

            // Close mobile menu when clicking on a link
            navMenu.addEventListener('click', (e) => {
                if (e.target.classList.contains('nav-link')) {
                    navToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            });
        }

        // Smooth scrolling for anchor links
        document.addEventListener('click', (e) => {
            if (e.target.tagName === 'A' && e.target.getAttribute('href')?.startsWith('#')) {
                e.preventDefault();
                const targetId = e.target.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    }

    bindUIEvents() {
        // Close toast notifications automatically
        this.setupAutoCloseToasts();
        
        // Handle form input animations
        this.setupFormAnimations();
        
        // Handle keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    setupAutoCloseToasts() {
        // Auto-close toasts after 5 seconds
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const toast = mutation.target;
                    if (toast.classList.contains('active')) {
                        setTimeout(() => {
                            if (toast.classList.contains('active')) {
                                hideToast();
                            }
                        }, 5000);
                    }
                }
            });
        });

        const toast = document.getElementById('toast');
        if (toast) {
            observer.observe(toast, { attributes: true });
        }
    }

    setupFormAnimations() {
        // Add focus/blur animations to form inputs
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', (e) => {
                const wrapper = e.target.closest('.form-group');
                if (wrapper) {
                    wrapper.classList.add('focused');
                }
            });

            input.addEventListener('blur', (e) => {
                const wrapper = e.target.closest('.form-group');
                if (wrapper) {
                    wrapper.classList.remove('focused');
                }
            });
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // ESC key to close modals or go back
            if (e.key === 'Escape') {
                if (this.currentScreen !== 'landing-screen') {
                    showHome();
                }
            }

            // Ctrl/Cmd + Enter to submit forms
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const activeForm = document.querySelector('.screen.active form');
                if (activeForm) {
                    const submitBtn = activeForm.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.click();
                    }
                }
            }
        });
    }

    async initializeApp() {
        // Initialize features that don't require authentication
        this.startAnimations();
        this.loadSampleData();
        
        // Check if user is already authenticated
        if (TokenManager.isLoggedIn()) {
            try {
                const isValid = await api.checkAuthStatus();
                if (isValid) {
                    // User is authenticated, load their dashboard
                    showDashboard();
                } else {
                    // Invalid token, show landing page
                    showHome();
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                showHome();
            }
        } else {
            showHome();
        }
    }

    startAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe elements that should animate on scroll
        const animateElements = document.querySelectorAll('.feature-card, .stat-card, .device-card');
        animateElements.forEach(el => observer.observe(el));
    }

    loadSampleData() {
        // Load sample dashboard data (replace with real API calls)
        this.updateDashboardStats();
        this.updateRecentActivity();
        this.updateDeviceStatus();
    }

    updateDashboardStats() {
        // Animate counter numbers
        const statNumbers = document.querySelectorAll('.stat-info h4');
        statNumbers.forEach((element, index) => {
            const finalValue = element.textContent;
            const isNumeric = /^\d+/.test(finalValue);
            
            if (isNumeric) {
                const value = parseInt(finalValue);
                this.animateCounter(element, 0, value, 1000 + (index * 200));
            }
        });
    }

    animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = Math.round(start + (end - start) * easeOutQuart);
            
            element.textContent = current + (element.textContent.includes('%') ? '%' : '');
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    }

    updateRecentActivity() {
        // Add timestamps to activity items
        const activityItems = document.querySelectorAll('.activity-item small');
        activityItems.forEach((item, index) => {
            const minutesAgo = [2, 15, 60][index] || Math.floor(Math.random() * 120);
            item.textContent = this.formatTimeAgo(minutesAgo);
        });
    }

    updateDeviceStatus() {
        // Simulate real-time device updates
        setInterval(() => {
            const deviceStatuses = document.querySelectorAll('.device-status.online span');
            deviceStatuses.forEach(status => {
                // Add pulse animation
                status.style.animation = 'none';
                setTimeout(() => {
                    status.style.animation = 'pulse 2s infinite';
                }, 10);
            });
        }, 30000); // Update every 30 seconds
    }

    formatTimeAgo(minutes) {
        if (minutes < 1) {
            return 'Just now';
        } else if (minutes < 60) {
            return `${minutes} minutes ago`;
        } else if (minutes < 1440) {
            const hours = Math.floor(minutes / 60);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            const days = Math.floor(minutes / 1440);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        }
    }

    showScreen(screenId) {
        // Hide all screens
        const screens = document.querySelectorAll('.screen');
        screens.forEach(screen => {
            screen.classList.remove('active');
        });

        // Show target screen
        const targetScreen = document.getElementById(screenId);
        if (targetScreen) {
            targetScreen.classList.add('active');
            this.currentScreen = screenId;
            
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
            // Focus first input if it's a form screen
            const firstInput = targetScreen.querySelector('input:not([readonly]):not([disabled])');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 300);
            }
        }
    }
}

// Screen navigation functions
function showScreen(screenId) {
    if (window.appManager) {
        window.appManager.showScreen(screenId);
    }
}

function showHome() {
    showScreen('landing-screen');
}

function showLogin() {
    showScreen('login-screen');
}

function showRegister() {
    showScreen('register-screen');
}

function showDashboard() {
    showScreen('dashboard-screen');
}

function showProfile() {
    showScreen('profile-screen');
}

function showVerification() {
    showScreen('verification-screen');
}

// Loading overlay functions
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// Toast notification functions
function showToast(type, title, message) {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toast-title');
    const toastText = document.getElementById('toast-text');
    const toastIcon = toast.querySelector('.toast-icon i');

    if (!toast || !toastTitle || !toastText || !toastIcon) return;

    // Set content
    toastTitle.textContent = title;
    toastText.textContent = message;

    // Set type and icon
    toast.className = `toast ${type} active`;
    
    const icons = {
        success: 'fas fa-check',
        error: 'fas fa-times',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    toastIcon.className = icons[type] || icons.info;
}

function hideToast() {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.classList.remove('active');
    }
}

// Utility functions
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Device detection
function isMobile() {
    return window.innerWidth <= 768;
}

function isTablet() {
    return window.innerWidth > 768 && window.innerWidth <= 1024;
}

function isDesktop() {
    return window.innerWidth > 1024;
}

// Local storage helpers
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

function loadFromStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultValue;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

// Performance monitoring
function measurePerformance(name, fn) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    console.log(`${name} took ${end - start} milliseconds`);
    return result;
}

// Error boundary for uncaught errors
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    
    // Don't show error toast for network errors during development
    if (!event.error?.message?.includes('NetworkError')) {
        showToast('error', 'Something went wrong', 'An unexpected error occurred. Please try again.');
    }
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Prevent the default handler that logs to console
    event.preventDefault();
    
    // Show user-friendly error message
    if (event.reason instanceof APIError) {
        showToast('error', 'Request Failed', event.reason.message);
    } else {
        showToast('error', 'Something went wrong', 'An unexpected error occurred. Please try again.');
    }
});

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.appManager = new AppManager();
});

// Export functions for global access
window.showScreen = showScreen;
window.showHome = showHome;
window.showLogin = showLogin;
window.showRegister = showRegister;
window.showDashboard = showDashboard;
window.showProfile = showProfile;
window.showVerification = showVerification;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showToast = showToast;
window.hideToast = hideToast;
window.debounce = debounce;
window.throttle = throttle;
window.isMobile = isMobile;
window.isTablet = isTablet;
window.isDesktop = isDesktop;
window.saveToStorage = saveToStorage;
window.loadFromStorage = loadFromStorage;
