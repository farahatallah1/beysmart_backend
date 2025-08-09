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

def create_tb_user(email, first_name, last_name, password):
    """Create a ThingsBoard user under the configured customer."""
    token = get_tb_token()
    # Request ThingsBoard to send activation email to the created user
    url = f"{settings.TB_BASE_URL}/api/user?sendActivationMail=true"
    headers = {"X-Authorization": f"Bearer {token}"}

    payload = {
        "email": email,
        "authority": "CUSTOMER_USER",
        "firstName": first_name,
        "lastName": last_name,
        "customerId": {"id": settings.TB_CUSTOMER_ID, "entityType": "CUSTOMER"},
        "additionalInfo": {
            "defaultDashboardId": None,
            "description": "Created from Django backend"
        }
    }

    res = requests.post(url, json=payload, headers=headers)
    res.raise_for_status()
    return res.json()
