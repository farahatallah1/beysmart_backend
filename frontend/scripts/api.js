// API Configuration
const API_CONFIG = {
    baseURL: 'http://localhost:8000/api',
    endpoints: {
        register: '/auth/register/',
        login: '/auth/login/',
        logout: '/auth/logout/',
        profile: '/auth/profile/',
        tokenRefresh: '/auth/token/refresh/',
        tokenVerify: '/auth/token/verify/',
        sendInvitation: '/auth/send-invitation/'
    }
};

// Token management
class TokenManager {
    static getAccessToken() {
        return localStorage.getItem('access_token');
    }

    static getRefreshToken() {
        return localStorage.getItem('refresh_token');
    }

    static setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
        }
    }

    static clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
    }

    static isLoggedIn() {
        return !!this.getAccessToken();
    }

    static async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.tokenRefresh}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh: refreshToken
                })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            this.setTokens(data.access, refreshToken);
            return data.access;
        } catch (error) {
            this.clearTokens();
            throw error;
        }
    }

    static async verifyToken() {
        const accessToken = this.getAccessToken();
        if (!accessToken) {
            return false;
        }

        try {
            const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.tokenVerify}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: accessToken
                })
            });

            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// API Client class
class APIClient {
    constructor() {
        this.baseURL = API_CONFIG.baseURL;
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        // Add authorization header if token exists
        const accessToken = TokenManager.getAccessToken();
        if (accessToken) {
            defaultHeaders['Authorization'] = `Bearer ${accessToken}`;
        }

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        };

        try {
            let response = await fetch(url, config);

            // If unauthorized and we have a refresh token, try to refresh
            if (response.status === 401 && TokenManager.getRefreshToken()) {
                try {
                    await TokenManager.refreshAccessToken();
                    // Retry the request with new token
                    config.headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
                    response = await fetch(url, config);
                } catch (refreshError) {
                    // Refresh failed, redirect to login
                    TokenManager.clearTokens();
                    showLogin();
                    throw new Error('Session expired. Please login again.');
                }
            }

            // Parse response
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                console.error('API Error Response:', {
                    status: response.status,
                    statusText: response.statusText,
                    data: data,
                    url: url,
                    method: config.method
                });
                throw new APIError(data.error || data.detail || 'Request failed', response.status, data);
            }

            return data;
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError(error.message || 'Network error occurred', 0);
        }
    }

    // Authentication methods
    async register(userData) {
        return this.makeRequest(API_CONFIG.endpoints.register, {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async login(credentials) {
        const response = await this.makeRequest(API_CONFIG.endpoints.login, {
            method: 'POST',
            body: JSON.stringify(credentials),
        });

        if (response.access && response.refresh) {
            TokenManager.setTokens(response.access, response.refresh);
            localStorage.setItem('user_data', JSON.stringify(response.user));
        }

        return response;
    }

    async logout() {
        const refreshToken = TokenManager.getRefreshToken();
        if (refreshToken) {
            try {
                await this.makeRequest(API_CONFIG.endpoints.logout, {
                    method: 'POST',
                    body: JSON.stringify({
                        refresh: refreshToken
                    }),
                });
            } catch (error) {
                console.warn('Logout request failed:', error);
            }
        }
        TokenManager.clearTokens();
    }

    async getProfile() {
        return this.makeRequest(API_CONFIG.endpoints.profile, {
            method: 'GET',
        });
    }

    async updateProfile(profileData) {
        return this.makeRequest(API_CONFIG.endpoints.profile, {
            method: 'PUT',
            body: JSON.stringify(profileData),
        });
    }

    async sendInvitation(email) {
        return this.makeRequest(API_CONFIG.endpoints.sendInvitation, {
            method: 'POST',
            body: JSON.stringify({ email }),
        });
    }

    // Utility methods
    async checkAuthStatus() {
        if (!TokenManager.isLoggedIn()) {
            return false;
        }

        try {
            const isValid = await TokenManager.verifyToken();
            if (!isValid) {
                // Try to refresh
                await TokenManager.refreshAccessToken();
                return true;
            }
            return true;
        } catch (error) {
            TokenManager.clearTokens();
            return false;
        }
    }
}

// Custom error class
class APIError extends Error {
    constructor(message, status, data = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

// Create global API instance
const api = new APIClient();

// Utility functions for form handling
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        // Handle empty strings and optional fields
        if (value === '' || value === null) {
            // For optional fields, only include them if they have values
            if (['birthday', 'gender', 'parent_customer_id'].includes(key)) {
                // Skip empty optional fields
                continue;
            } else {
                // For required fields, keep empty string
                data[key] = '';
            }
        } else {
            data[key] = value;
        }
    }
    
    return data;
}

function populateForm(form, data) {
    const elements = form.elements;
    
    for (let element of elements) {
        const name = element.name;
        if (name && data.hasOwnProperty(name)) {
            if (element.type === 'checkbox') {
                element.checked = !!data[name];
            } else if (element.type === 'radio') {
                element.checked = element.value === data[name];
            } else {
                element.value = data[name] || '';
            }
        }
    }
}

// User data management
class UserManager {
    static getCurrentUser() {
        const userData = localStorage.getItem('user_data');
        return userData ? JSON.parse(userData) : null;
    }

    static updateCurrentUser(userData) {
        localStorage.setItem('user_data', JSON.stringify(userData));
    }

    static clearCurrentUser() {
        localStorage.removeItem('user_data');
    }

    static isUserApproved() {
        const user = this.getCurrentUser();
        return user && user.is_approved;
    }

    static getUserType() {
        const user = this.getCurrentUser();
        return user ? user.user_type : null;
    }

    static getUserDisplayName() {
        const user = this.getCurrentUser();
        if (!user) return 'Guest';
        return user.first_name && user.last_name 
            ? `${user.first_name} ${user.last_name}`
            : user.username;
    }
}

// Form validation utilities
class FormValidator {
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    static validatePassword(password) {
        // At least 8 characters, contains letter and number
        const minLength = password.length >= 8;
        const hasLetter = /[a-zA-Z]/.test(password);
        const hasNumber = /\d/.test(password);
        
        return {
            valid: minLength && hasLetter && hasNumber,
            minLength,
            hasLetter,
            hasNumber
        };
    }

    static validateUsername(username) {
        // 3-30 characters, alphanumeric and underscore only
        const re = /^[a-zA-Z0-9_]{3,30}$/;
        return re.test(username);
    }

    static validateRequired(value) {
        return value && value.trim().length > 0;
    }

    static validateForm(form, rules) {
        const errors = {};
        const formData = new FormData(form);

        for (const [field, validators] of Object.entries(rules)) {
            const value = formData.get(field);
            
            for (const validator of validators) {
                const result = validator(value);
                if (result !== true) {
                    if (!errors[field]) errors[field] = [];
                    errors[field].push(result);
                }
            }
        }

        return {
            isValid: Object.keys(errors).length === 0,
            errors
        };
    }
}

// Export for use in other scripts
window.api = api;
window.TokenManager = TokenManager;
window.UserManager = UserManager;
window.FormValidator = FormValidator;
window.APIError = APIError;
window.serializeForm = serializeForm;
window.populateForm = populateForm;
