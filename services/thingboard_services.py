import requests
from django.conf import settings

def get_tb_token():
    """Login as ThingsBoard admin and return JWT token."""
    url = f"{settings.TB_BASE_URL}/api/auth/login"
    payload = {
        "username": settings.TB_ADMIN_EMAIL,
        "password": settings.TB_ADMIN_PASSWORD
    }
    res = requests.post(url, json=payload)
    res.raise_for_status()
    return res.json()["token"]

def create_tb_user(email, first_name, last_name, user_type='CUSTOMER_USER', parent_customer_id=None):
    """Create a ThingsBoard user based on user type."""
    token = get_tb_token()
    
    if user_type == 'CUSTOMER':
        # Create a new customer
        url = f"{settings.TB_BASE_URL}/api/customer"
        payload = {
            "title": f"{first_name} {last_name}",
            "email": email,
            "additionalInfo": {
                "description": "Created from Django backend",
                "firstName": first_name,
                "lastName": last_name
            }
        }
    else:
        # Create a customer user under existing customer
        url = f"{settings.TB_BASE_URL}/api/user?sendActivationMail=false"
        payload = {
            "email": email,
            "authority": "CUSTOMER_USER",
            "firstName": first_name,
            "lastName": last_name,
            "customerId": {"id": parent_customer_id, "entityType": "CUSTOMER"},
            "additionalInfo": {
                "description": "Created from Django backend"
            }
        }
    
    headers = {"X-Authorization": f"Bearer {token}"}
    res = requests.post(url, json=payload, headers=headers)
    res.raise_for_status()
    return res.json()

def get_customer_by_email(email):
    """Get customer information by email."""
    token = get_tb_token()
    url = f"{settings.TB_BASE_URL}/api/customers"
    headers = {"X-Authorization": f"Bearer {token}"}
    
    # Search for customer by email
    params = {"email": email}
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    
    customers = res.json()
    if customers and len(customers) > 0:
        return customers[0]  # Return first matching customer
    return None

def get_customer_id_by_email(email):
    """Get customer ID by email for customer users."""
    customer = get_customer_by_email(email)
    if customer:
        return customer.get('id', {}).get('id')
    return None