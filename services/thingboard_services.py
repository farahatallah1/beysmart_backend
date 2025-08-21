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

def create_tb_user(email, first_name, last_name, user_type=None, parent_customer_id=None):
    """
    Create a ThingsBoard user.
    
    - By default → creates a CUSTOMER (new customer tenant in TB).
    - If called with user_type='CUSTOMER_USER' and parent_customer_id → 
      creates a CUSTOMER_USER under that customer.
    """
    token = get_tb_token()
    headers = {"X-Authorization": f"Bearer {token}"}

    if user_type == "CUSTOMER_USER" and parent_customer_id:
        # Create a customer user under an existing customer
        url = f"{settings.TB_BASE_URL}/api/user?sendActivationMail=false"
        payload = {
            "email": email,
            "authority": "CUSTOMER_USER",
            "firstName": first_name or "",
            "lastName": last_name or "",
            "customerId": {"id": parent_customer_id, "entityType": "CUSTOMER"},
            "additionalInfo": {
                "description": "Created from Django backend"
            }
        }
    else:
        # Default → create a new customer
        url = f"{settings.TB_BASE_URL}/api/customer"
        payload = {
            "title": f"{first_name} {last_name}" if (first_name or last_name) else email,
            "email": email,
            "additionalInfo": {
                "description": "Created from Django backend",
                "firstName": first_name or "",
                "lastName": last_name or ""
            }
        }

    res = requests.post(url, json=payload, headers=headers)
    res.raise_for_status()
    return res.json()

def get_customer_by_email(email):
    """Get customer information by email (ThingsBoard has no direct email filter, so this may need refinement)."""
    token = get_tb_token()
    url = f"{settings.TB_BASE_URL}/api/customers?pageSize=100&page=0"
    headers = {"X-Authorization": f"Bearer {token}"}

    res = requests.get(url, headers=headers)
    res.raise_for_status()
    
    customers = res.json().get("data", [])
    for c in customers:
        if c.get("email") == email:
            return c
    return None

def get_customer_id_by_email(email):
    """Get customer ID by email for customer users."""
    customer = get_customer_by_email(email)
    if customer:
        return customer.get("id", {}).get("id")
    return None
