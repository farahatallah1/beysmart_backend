# Beysmart Backend API Documentation

## Authentication Endpoints

### 1. Register User
**POST** `/api/auth/register/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123",
    "confirm_password": "securepassword123",
    "first_name": "Test",
    "last_name": "User",
    "birthday": "1990-01-01",
    "gender": "Male",
    "user_type": "CUSTOMER",
    "parent_customer_id": null
}
```

**Response (201 Created):**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "birthday": "1990-01-01",
    "gender": "Male",
    "user_type": "CUSTOMER"
}
```

### 2. Login
**POST** `/api/auth/login/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "username": "test@example.com",
    "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "user_type": "CUSTOMER",
        "is_approved": true
    }
}
```

**Error Response (401 Unauthorized):**
```json
{
    "error": "Invalid credentials",
    "detail": "Error message"
}
```

### 3. Refresh Token
**POST** `/api/auth/token/refresh/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 4. Verify Token
**POST** `/api/auth/token/verify/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{}
```

### 5. Logout
**POST** `/api/auth/logout/`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully logged out"
}
```

### 6. User Profile
**GET/PUT** `/api/auth/profile/`

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**GET Response (200 OK):**
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "birthday": "1990-01-01",
    "gender": "Male",
    "user_type": "CUSTOMER",
    "parent_customer_id": null,
    "is_approved": true,
    "approved_at": null,
    "date_joined": "2024-01-15T10:30:00Z"
}
```

**PUT Request Body (partial update allowed):**
```json
{
    "first_name": "Updated",
    "last_name": "Name",
    "birthday": "1991-01-01",
    "gender": "Female"
}
```

## User Types

- **CUSTOMER**: A customer who owns devices and can invite customer users
- **CUSTOMER_USER**: A user under a customer who can access customer's devices

## Authentication Flow

1. User registers with `/api/auth/register/`
2. Email verification is sent (user account is inactive until verified)
3. User verifies email through verification link
4. If user type is CUSTOMER_USER, they need approval from the parent customer
5. Once approved and verified, user can login with `/api/auth/login/`
6. Use the access token in Authorization header for protected endpoints
7. Refresh token when needed with `/api/auth/token/refresh/`
8. Logout to blacklist refresh token with `/api/auth/logout/`

## Error Codes

- **400**: Bad Request - Invalid data
- **401**: Unauthorized - Invalid credentials or token
- **403**: Forbidden - Account not approved or insufficient permissions
- **404**: Not Found - Resource not found
- **500**: Internal Server Error

## ThingsBoard Integration

The backend automatically creates users in ThingsBoard when:
- User email is verified successfully
- User type and parent customer information is validated

## Environment Variables Required

See `env_example.txt` for all required environment variables.


