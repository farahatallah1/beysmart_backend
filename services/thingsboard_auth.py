import requests
from django.conf import settings

class ThingsBoardAuth:
    """ThingsBoard authentication and user verification"""
    
    def __init__(self, tenant_token=None):
        self.tenant_token = tenant_token or self.get_tenant_token()
        # Use thingsboard.cloud since you have a token from there
        self.base_url = getattr(settings, 'TB_BASE_URL', None) or 'https://thingsboard.cloud'
    
    def get_tenant_token(self):
        """Get tenant admin token from settings or environment"""
        # For now, we'll use the provided token
        # In production, this should come from secure storage
        return "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJoYXplbW1haG1vdWQ1MTJAZ21haWwuY29tIiwidXNlcklkIjoiNDhkYTA3OTAtNzgzYS0xMWYwLWE0MTMtYjM4ZWM5NGQxNDY1Iiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJzZXNzaW9uSWQiOiJkZWNjZDk2YS04YzU2LTQwYjMtOTE3MS03ODc1MWU1Yzk5ZGYiLCJleHAiOjE3NTUyMjg4MzMsImlzcyI6InRoaW5nc2JvYXJkLmNsb3VkIiwiaWF0IjoxNzU1MjAwMDMzLCJmaXJzdE5hbWUiOiJoYXplbSIsImxhc3ROYW1lIjoibWFobW91ZCIsImVuYWJsZWQiOnRydWUsImlzUHVibGljIjpmYWxzZSwiaXNCaWxsaW5nU2VydmljZSI6ZmFsc2UsInByaXZhY3lQb2xpY3lBY2NlcHRlZCI6dHJ1ZSwidGVybXNPZlVzZUFjY2VwdGVkIjp0cnVlLCJ0ZW5hbnRJZCI6IjQ4YWI1NjcwLTc4M2EtMTFmMC1hNDEzLWIzOGVjOTRkMTQ2NSIsImN1c3RvbWVySWQiOiIxMzgxNDAwMC0xZGQyLTExYjItODA4MC04MDgwODA4MDgwODAifQ.nt_o152xsR5Uf1IasI7_vNCSC4w3_HtWFVsxhPgN4QTu9DwIGjA0qRJnS7RIUJyYYMBlSpQ5yCzJNO3MhwmWRg"
    
    def get_headers(self):
        """Get request headers with authorization"""
        return {
            "X-Authorization": f"Bearer {self.tenant_token}",
            "Content-Type": "application/json"
        }
    
    def find_user_by_email(self, email):
        """Find user in ThingsBoard by email"""
        try:
            # First, check if user exists as a customer
            customer = self.find_customer_by_email(email)
            if customer:
                return {
                    'found': True,
                    'type': 'CUSTOMER',
                    'data': customer,
                    'id': customer.get('id', {}).get('id'),
                    'name': customer.get('title', 'Unknown')
                }
            
            # Then check if user exists as a customer user
            user = self.find_customer_user_by_email(email)
            if user:
                return {
                    'found': True,
                    'type': 'CUSTOMER_USER',
                    'data': user,
                    'id': user.get('id', {}).get('id'),
                    'name': f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                }
            
            return {
                'found': False,
                'type': None,
                'data': None,
                'id': None,
                'name': None
            }
            
        except Exception as e:
            print(f"Error finding user in ThingsBoard: {e}")
            return {
                'found': False,
                'error': str(e),
                'type': None,
                'data': None,
                'id': None,
                'name': None
            }
    
    def find_customer_by_email(self, email):
        """Find customer by email"""
        try:
            url = f"{self.base_url}/api/customers"
            params = {"pageSize": 100, "page": 0}
            
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            customers_data = response.json()
            customers = customers_data.get('data', [])
            
            # Search for customer with matching email
            for customer in customers:
                if customer.get('email') == email:
                    return customer
            
            return None
            
        except Exception as e:
            print(f"Error searching customers: {e}")
            return None
    
    def find_customer_user_by_email(self, email):
        """Find customer user by email"""
        try:
            url = f"{self.base_url}/api/users"
            params = {
                "pageSize": 100, 
                "page": 0,
                "textSearch": email
            }
            
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            users_data = response.json()
            users = users_data.get('data', [])
            
            # Search for user with exact email match
            for user in users:
                if user.get('email') == email:
                    return user
            
            return None
            
        except Exception as e:
            print(f"Error searching customer users: {e}")
            return None
    
    def verify_user_access(self, email, user_type):
        """Verify user has appropriate access in ThingsBoard"""
        tb_user = self.find_user_by_email(email)
        
        if not tb_user['found']:
            return {
                'verified': False,
                'message': 'User not found in ThingsBoard',
                'tb_data': None
            }
        
        # Check if ThingsBoard user type matches Django user type
        if tb_user['type'] != user_type:
            return {
                'verified': False,
                'message': f"User type mismatch: Django={user_type}, ThingsBoard={tb_user['type']}",
                'tb_data': tb_user
            }
        
        return {
            'verified': True,
            'message': 'User verified in ThingsBoard',
            'tb_data': tb_user
        }
    
    def create_thingsboard_user(self, email, first_name, last_name, user_type, parent_customer_id=None):
        """Create user in ThingsBoard"""
        try:
            if user_type == 'CUSTOMER':
                return self.create_customer(email, first_name, last_name)
            else:
                return self.create_customer_user(email, first_name, last_name, parent_customer_id)
        except Exception as e:
            print(f"Error creating ThingsBoard user: {e}")
            return None
    
    def create_customer(self, email, first_name, last_name):
        """Create a new customer in ThingsBoard"""
        url = f"{self.base_url}/api/customer"
        payload = {
            "title": f"{first_name} {last_name}",
            "email": email,
            "additionalInfo": {
                "description": f"Customer created from Django backend for {email}",
                "firstName": first_name,
                "lastName": last_name
            }
        }
        
        response = requests.post(url, json=payload, headers=self.get_headers())
        response.raise_for_status()
        return response.json()
    
    def create_customer_user(self, email, first_name, last_name, customer_id):
        """Create a customer user in ThingsBoard"""
        url = f"{self.base_url}/api/user?sendActivationMail=false"
        payload = {
            "email": email,
            "authority": "CUSTOMER_USER",
            "firstName": first_name,
            "lastName": last_name,
            "customerId": {"id": customer_id, "entityType": "CUSTOMER"},
            "additionalInfo": {
                "description": f"Customer user created from Django backend for {email}"
            }
        }
        
        response = requests.post(url, json=payload, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

# Global instance
tb_auth = ThingsBoardAuth()
