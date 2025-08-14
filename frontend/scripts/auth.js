// Authentication handling and form management

class AuthManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkInitialAuthState();
    }

    bindEvents() {
        // Form submissions
        this.bindFormSubmission('login-form', this.handleLogin.bind(this));
        this.bindFormSubmission('register-form', this.handleRegister.bind(this));
        this.bindFormSubmission('profile-form', this.handleProfileUpdate.bind(this));

        // Real-time validation
        this.bindFieldValidation();
    }

    bindFormSubmission(formId, handler) {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                handler(form);
            });
        }
    }

    bindFieldValidation() {
        // Email validation
        const emailFields = document.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            field.addEventListener('blur', this.validateEmailField.bind(this));
        });

        // Password validation
        const passwordFields = document.querySelectorAll('input[type="password"]');
        passwordFields.forEach(field => {
            if (field.name === 'password') {
                field.addEventListener('input', this.validatePasswordField.bind(this));
            }
            if (field.name === 'confirm_password') {
                field.addEventListener('input', this.validateConfirmPassword.bind(this));
            }
        });

        // Username validation
        const usernameField = document.getElementById('username');
        if (usernameField) {
            usernameField.addEventListener('blur', this.validateUsernameField.bind(this));
        }
    }

    async checkInitialAuthState() {
        if (TokenManager.isLoggedIn()) {
            try {
                const isValid = await api.checkAuthStatus();
                if (isValid) {
                    showDashboard();
                    await this.loadUserProfile();
                } else {
                    showLogin();
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                showLogin();
            }
        }
    }

    async handleLogin(form) {
        showLoading();
        
        try {
            const formData = serializeForm(form);
            
            // Log what we're sending
            console.log('Login form data being sent:', formData);
            
            // Validate required fields
            if (!formData.username || !formData.password) {
                throw new Error('Please fill in all required fields');
            }

            const response = await api.login(formData);
            
            hideLoading();
            showToast('success', 'Login Successful', 'Welcome back!');
            
            // Check if user is approved
            if (!response.user.is_approved) {
                this.showApprovalPending();
                return;
            }

            showDashboard();
            await this.loadUserProfile();
            
        } catch (error) {
            hideLoading();
            console.error('Login error:', error);
            
            if (error instanceof APIError) {
                if (error.data && error.data.detail) {
                    showToast('error', 'Login Failed', error.data.detail);
                } else {
                    showToast('error', 'Login Failed', error.message);
                }
            } else {
                showToast('error', 'Login Failed', 'An unexpected error occurred');
            }
        }
    }

    async handleRegister(form) {
        showLoading();
        
        try {
            const formData = serializeForm(form);
            
            // Clean up form data based on user type
            if (formData.user_type === 'CUSTOMER') {
                // Remove parent_customer_id for regular customers
                delete formData.parent_customer_id;
            }
            
            // Log the form data being sent
            console.log('Registration form data:', formData);
            
            // Validate form
            const validation = this.validateRegistrationForm(formData);
            if (!validation.isValid) {
                throw new Error(validation.message);
            }

            const response = await api.register(formData);
            
            hideLoading();
            showToast('success', 'Registration Successful', 'Please check your email for verification instructions.');
            
            // Show verification screen
            this.showEmailVerificationRequired(formData.email);
            
        } catch (error) {
            hideLoading();
            console.error('Registration error:', error);
            
            if (error instanceof APIError) {
                // Handle specific validation errors
                if (error.data && typeof error.data === 'object') {
                    console.log('Validation errors from backend:', error.data);
                    
                    // Get the first error message
                    const errorKeys = Object.keys(error.data);
                    if (errorKeys.length > 0) {
                        const firstKey = errorKeys[0];
                        const firstError = error.data[firstKey];
                        const errorMessage = Array.isArray(firstError) ? firstError[0] : firstError;
                        showToast('error', 'Registration Failed', `${firstKey}: ${errorMessage}`);
                    } else {
                        showToast('error', 'Registration Failed', error.message);
                    }
                } else {
                    showToast('error', 'Registration Failed', error.message);
                }
            } else {
                showToast('error', 'Registration Failed', error.message);
            }
        }
    }

    async handleProfileUpdate(form) {
        showLoading();
        
        try {
            const formData = serializeForm(form);
            
            // Remove readonly fields
            delete formData.username;
            delete formData.email;
            
            const response = await api.updateProfile(formData);
            
            // Update stored user data
            UserManager.updateCurrentUser(response);
            
            hideLoading();
            showToast('success', 'Profile Updated', 'Your profile has been updated successfully.');
            
        } catch (error) {
            hideLoading();
            console.error('Profile update error:', error);
            showToast('error', 'Update Failed', 'Failed to update profile. Please try again.');
        }
    }

    async loadUserProfile() {
        try {
            const profile = await api.getProfile();
            UserManager.updateCurrentUser(profile);
            this.updateUIWithUserData(profile);
        } catch (error) {
            console.error('Failed to load profile:', error);
        }
    }

    updateUIWithUserData(userData) {
        // Update dashboard user info
        const userName = document.getElementById('user-name');
        const userEmail = document.getElementById('user-email');
        const userTypeBadge = document.getElementById('user-type-badge');

        if (userName) {
            userName.textContent = `Welcome, ${userData.first_name || userData.username}!`;
        }
        if (userEmail) {
            userEmail.textContent = userData.email;
        }
        if (userTypeBadge) {
            userTypeBadge.textContent = userData.user_type === 'CUSTOMER' ? 'Customer' : 'Customer User';
        }

        // Update profile form
        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            populateForm(profileForm, userData);
            
            // Update readonly fields
            document.getElementById('profile-user-type').textContent = 
                userData.user_type === 'CUSTOMER' ? 'Customer' : 'Customer User';
            
            const statusElement = document.getElementById('profile-status');
            if (statusElement) {
                statusElement.textContent = userData.is_approved ? 'Approved' : 'Pending Approval';
                statusElement.className = `status-badge ${userData.is_approved ? 'approved' : 'pending'}`;
            }
            
            const joinDateElement = document.getElementById('profile-join-date');
            if (joinDateElement && userData.date_joined) {
                const date = new Date(userData.date_joined);
                joinDateElement.textContent = date.toLocaleDateString();
            }
        }

        // Update navigation
        this.updateNavigationForLoggedInUser();
    }

    updateNavigationForLoggedInUser() {
        const navMenu = document.getElementById('nav-menu');
        const logoutBtn = document.getElementById('logout-btn');
        
        // Hide login/register links
        const loginLinks = navMenu.querySelectorAll('.nav-link:not(#logout-btn)');
        loginLinks.forEach(link => {
            if (link.textContent.includes('Login') || link.textContent.includes('Register')) {
                link.style.display = 'none';
            }
        });
        
        // Show logout button
        if (logoutBtn) {
            logoutBtn.style.display = 'block';
        }
    }

    showEmailVerificationRequired(email) {
        const screen = document.getElementById('verification-screen');
        const icon = document.getElementById('verification-icon');
        const title = document.getElementById('verification-title');
        const message = document.getElementById('verification-message');

        if (icon) {
            icon.innerHTML = '<i class="fas fa-envelope"></i>';
        }
        if (title) {
            title.textContent = 'Email Verification Required';
        }
        if (message) {
            message.textContent = `We've sent a verification email to ${email}. Please check your inbox and click the verification link to activate your account.`;
        }

        showScreen('verification-screen');
    }

    showApprovalPending() {
        const screen = document.getElementById('verification-screen');
        const icon = document.getElementById('verification-icon');
        const title = document.getElementById('verification-title');
        const message = document.getElementById('verification-message');

        if (icon) {
            icon.innerHTML = '<i class="fas fa-clock"></i>';
        }
        if (title) {
            title.textContent = 'Approval Pending';
        }
        if (message) {
            message.textContent = 'Your account is pending approval from your customer administrator. You will receive an email once your account is approved.';
        }

        showScreen('verification-screen');
    }

    validateRegistrationForm(data) {
        // Required fields
        const requiredFields = ['username', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 'user_type'];
        for (const field of requiredFields) {
            if (!data[field] || data[field].trim() === '') {
                return { isValid: false, message: `${field.replace('_', ' ')} is required` };
            }
        }

        // Email validation
        if (!FormValidator.validateEmail(data.email)) {
            return { isValid: false, message: 'Please enter a valid email address' };
        }

        // Username validation
        if (!FormValidator.validateUsername(data.username)) {
            return { isValid: false, message: 'Username must be 3-30 characters, letters, numbers, and underscores only' };
        }

        // Password validation
        const passwordCheck = FormValidator.validatePassword(data.password);
        if (!passwordCheck.valid) {
            return { isValid: false, message: 'Password must be at least 8 characters with letters and numbers' };
        }

        // Password confirmation
        if (data.password !== data.confirm_password) {
            return { isValid: false, message: 'Passwords do not match' };
        }

        // Customer user validation
        if (data.user_type === 'CUSTOMER_USER' && (!data.parent_customer_id || data.parent_customer_id.trim() === '')) {
            return { isValid: false, message: 'Customer ID is required for Customer User accounts' };
        }

        // For Customer accounts, remove parent_customer_id if present
        if (data.user_type === 'CUSTOMER' && data.parent_customer_id) {
            delete data.parent_customer_id;
        }

        return { isValid: true };
    }

    validateEmailField(event) {
        const field = event.target;
        const isValid = FormValidator.validateEmail(field.value);
        this.updateFieldValidation(field, isValid, 'Please enter a valid email address');
    }

    validatePasswordField(event) {
        const field = event.target;
        const validation = FormValidator.validatePassword(field.value);
        let message = '';
        
        if (!validation.minLength) message += 'At least 8 characters. ';
        if (!validation.hasLetter) message += 'Must contain letters. ';
        if (!validation.hasNumber) message += 'Must contain numbers. ';
        
        this.updateFieldValidation(field, validation.valid, message.trim());
    }

    validateConfirmPassword(event) {
        const field = event.target;
        const passwordField = document.getElementById('password');
        const isValid = passwordField && field.value === passwordField.value;
        this.updateFieldValidation(field, isValid, 'Passwords do not match');
    }

    validateUsernameField(event) {
        const field = event.target;
        const isValid = FormValidator.validateUsername(field.value);
        this.updateFieldValidation(field, isValid, '3-30 characters, letters, numbers, and underscores only');
    }

    updateFieldValidation(field, isValid, errorMessage) {
        const wrapper = field.closest('.form-group');
        if (!wrapper) return;

        // Remove existing validation classes and messages
        wrapper.classList.remove('has-error', 'has-success');
        const existingError = wrapper.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        if (field.value.trim() === '') {
            // Empty field, no validation styling
            return;
        }

        if (isValid) {
            wrapper.classList.add('has-success');
            field.style.borderColor = 'var(--success-color)';
        } else {
            wrapper.classList.add('has-error');
            field.style.borderColor = 'var(--error-color)';
            
            // Add error message
            const errorElement = document.createElement('small');
            errorElement.className = 'field-error';
            errorElement.style.color = 'var(--error-color)';
            errorElement.textContent = errorMessage;
            wrapper.appendChild(errorElement);
        }
    }

    async handleLogout() {
        try {
            await api.logout();
            showToast('success', 'Logged Out', 'You have been successfully logged out.');
            showHome();
            this.resetNavigation();
        } catch (error) {
            console.error('Logout error:', error);
            // Even if logout request fails, clear local data
            TokenManager.clearTokens();
            UserManager.clearCurrentUser();
            showHome();
            this.resetNavigation();
        }
    }

    resetNavigation() {
        const navMenu = document.getElementById('nav-menu');
        const logoutBtn = document.getElementById('logout-btn');
        
        // Show login/register links
        const loginLinks = navMenu.querySelectorAll('.nav-link:not(#logout-btn)');
        loginLinks.forEach(link => {
            link.style.display = 'block';
        });
        
        // Hide logout button
        if (logoutBtn) {
            logoutBtn.style.display = 'none';
        }
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
});

// Global functions for easy access
window.logout = function() {
    if (window.authManager) {
        window.authManager.handleLogout();
    }
};

window.toggleCustomerField = function() {
    const userTypeSelect = document.getElementById('user-type');
    const customerField = document.getElementById('customer-field');
    
    if (userTypeSelect && customerField) {
        if (userTypeSelect.value === 'CUSTOMER_USER') {
            customerField.style.display = 'block';
            document.getElementById('parent-customer').required = true;
        } else {
            customerField.style.display = 'none';
            document.getElementById('parent-customer').required = false;
        }
    }
};

window.togglePassword = function(fieldId) {
    const field = document.getElementById(fieldId);
    const button = field.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (field.type === 'password') {
        field.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        field.type = 'password';
        icon.className = 'fas fa-eye';
    }
};
