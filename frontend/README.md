# Beysmart Frontend Sample Screens

This directory contains modern, responsive sample screens for the Beysmart IoT management platform. The frontend is built with vanilla HTML, CSS, and JavaScript and integrates with the Django REST API backend.

## 🚀 Features

### ✨ Modern UI/UX
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Dark/Light Theme**: Clean, modern design with CSS custom properties
- **Smooth Animations**: Fade-in transitions, hover effects, and loading states
- **Professional Typography**: Uses Inter font family for optimal readability

### 🔐 Authentication Flow
- **User Registration**: Complete registration form with validation
- **Login System**: Secure JWT-based authentication
- **Email Verification**: Email verification workflow
- **Approval System**: Customer user approval workflow
- **Profile Management**: User profile editing and viewing

### 📱 Screens Included

1. **Landing Page** (`index.html`)
   - Hero section with gradient background
   - Feature showcase
   - Call-to-action buttons

2. **Login Screen**
   - Email/password form
   - Real-time validation
   - Error handling
   - Remember me functionality

3. **Registration Screen**
   - Multi-step form with validation
   - User type selection (Customer/Customer User)
   - Password strength indicator
   - Terms acceptance

4. **Dashboard Screen**
   - User statistics overview
   - Device status monitoring
   - Recent activity feed
   - Quick actions panel

5. **Profile Screen**
   - Personal information editing
   - Account status display
   - Security settings
   - Activity history

6. **Verification Screen**
   - Email verification status
   - Approval pending states
   - Success/error messages

### 🛠 Technical Features

- **JWT Token Management**: Automatic token refresh and validation
- **API Integration**: Complete REST API client with error handling
- **Form Validation**: Real-time client-side validation
- **Loading States**: User-friendly loading indicators
- **Toast Notifications**: Non-intrusive success/error messages
- **Mobile Navigation**: Responsive hamburger menu
- **Keyboard Shortcuts**: ESC to go back, Ctrl+Enter to submit forms

## 🏗 Project Structure

```
frontend/
├── index.html              # Main HTML file with all screens
├── styles/
│   └── main.css            # Complete stylesheet with animations
├── scripts/
│   ├── api.js              # API client and utilities
│   ├── auth.js             # Authentication handling
│   └── main.js             # Main app logic and UI management
└── README.md               # This file
```

## 🚦 Getting Started

### Prerequisites
- Django backend running on `http://localhost:8000`
- Modern web browser with ES6+ support

### Installation

1. **Start the Django backend**:
   ```bash
   cd beysmart_backend
   python manage.py runserver
   ```

2. **Open the frontend**:
   - Open `index.html` in your web browser
   - Or serve it with a local server:
     ```bash
     # Using Python
     python -m http.server 3000
     
     # Using Node.js
     npx serve . -p 3000
     ```

3. **Access the application**:
   - Navigate to `http://localhost:3000` (if using a server)
   - Or open `index.html` directly in your browser

## 🎯 Usage Guide

### First Time Setup

1. **Start with Registration**:
   - Click "Get Started" or "Register"
   - Fill out the registration form
   - Choose account type (Customer or Customer User)
   - Submit and check email for verification

2. **Email Verification**:
   - Check your email for verification link
   - Click the verification link
   - Return to the application and login

3. **Login**:
   - Use your email and password
   - System will redirect to dashboard if approved
   - Or show approval pending screen if waiting for approval

### Navigation

- **Home**: Landing page with features
- **Login**: Sign in to your account
- **Register**: Create a new account
- **Dashboard**: Main user interface (after login)
- **Profile**: Manage account settings
- **Logout**: Sign out of the application

### API Configuration

The frontend is configured to connect to the Django backend at `http://localhost:8000/api`. To change this:

1. Open `scripts/api.js`
2. Modify the `API_CONFIG.baseURL` value:
   ```javascript
   const API_CONFIG = {
       baseURL: 'https://your-backend-url.com/api',
       // ... rest of config
   };
   ```

## 🎨 Customization

### Styling

The CSS uses custom properties (CSS variables) for easy theming:

```css
:root {
    --primary-color: #667eea;    /* Main brand color */
    --secondary-color: #764ba2;  /* Secondary brand color */
    --accent-color: #f093fb;     /* Accent color */
    --success-color: #10b981;    /* Success states */
    --warning-color: #f59e0b;    /* Warning states */
    --error-color: #ef4444;      /* Error states */
    /* ... more variables */
}
```

### Adding New Screens

1. **Add HTML structure** in `index.html`:
   ```html
   <div class="screen" id="new-screen">
       <!-- Your screen content -->
   </div>
   ```

2. **Add navigation function** in `main.js`:
   ```javascript
   function showNewScreen() {
       showScreen('new-screen');
   }
   ```

3. **Add styling** in `main.css`:
   ```css
   #new-screen {
       /* Your screen styles */
   }
   ```

## 📱 Responsive Breakpoints

- **Mobile**: `≤ 768px`
- **Tablet**: `769px - 1024px`
- **Desktop**: `≥ 1025px`

## 🔧 API Integration

### Available API Methods

```javascript
// Authentication
await api.login({ username: 'email', password: 'password' });
await api.register(userData);
await api.logout();

// Profile Management
await api.getProfile();
await api.updateProfile(profileData);

// Invitations
await api.sendInvitation('email@example.com');

// Token Management
TokenManager.getAccessToken();
TokenManager.setTokens(access, refresh);
TokenManager.clearTokens();
```

### Error Handling

The API client includes comprehensive error handling:

```javascript
try {
    const result = await api.login(credentials);
    showToast('success', 'Login Successful', 'Welcome back!');
} catch (error) {
    if (error instanceof APIError) {
        showToast('error', 'Login Failed', error.message);
    }
}
```

## 🔒 Security Features

- **JWT Token Storage**: Secure token management in localStorage
- **Automatic Token Refresh**: Seamless session management
- **Input Validation**: Client-side validation for all forms
- **CSRF Protection**: Integration with Django's CSRF tokens
- **Secure Headers**: Proper security headers configuration

## 🎭 User Experience Features

- **Loading States**: Visual feedback during API calls
- **Form Validation**: Real-time validation with error messages
- **Toast Notifications**: Non-intrusive success/error messages
- **Keyboard Navigation**: Full keyboard accessibility
- **Mobile Optimized**: Touch-friendly interface on mobile devices

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure Django CORS settings allow your frontend domain
   - Check `settings.py` for `CORS_ALLOWED_ORIGINS`

2. **API Connection Issues**:
   - Verify Django backend is running on port 8000
   - Check browser console for network errors
   - Confirm API endpoints in `api.js` match backend URLs

3. **Token Errors**:
   - Clear localStorage and try logging in again
   - Check token expiration settings in Django

4. **Email Issues**:
   - Verify email configuration in Django settings
   - Check spam folder for verification emails

## 🚀 Performance Optimization

- **Lazy Loading**: Images and components loaded on demand
- **Debounced Input**: Reduced API calls during typing
- **Efficient Animations**: Hardware-accelerated CSS transitions
- **Minimal Dependencies**: No external JavaScript frameworks

## 📚 Browser Support

- **Chrome**: 88+
- **Firefox**: 85+
- **Safari**: 14+
- **Edge**: 88+

## 🔄 Updates and Maintenance

To update the frontend:

1. **CSS Updates**: Modify `styles/main.css`
2. **JavaScript Features**: Update relevant files in `scripts/`
3. **HTML Structure**: Modify `index.html`
4. **API Changes**: Update endpoint configurations in `api.js`

## 📞 Support

For issues or questions:

1. Check the Django backend logs
2. Review browser console for JavaScript errors
3. Verify API endpoint configurations
4. Test with different browsers

## 🏆 Best Practices

- **Always validate user input** both client and server-side
- **Use HTTPS** in production environments
- **Implement proper error boundaries** for graceful degradation
- **Test across multiple devices** and browsers
- **Keep dependencies updated** for security patches

---

**Built with ❤️ for the Beysmart IoT Platform**
