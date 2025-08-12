from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Create your models here.
class CustomUser(AbstractUser):
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ], null=True, blank=True)

    # email must be unique
    email = models.EmailField(unique=True)

    user_type = models.CharField(
        max_length=20, 
        choices=[
            ('CUSTOMER', 'Customer'),
            ('CUSTOMER_USER', 'Customer User')
        ],
        default='CUSTOMER_USER'
    )
    
    # If they choose to be a customer user, they need to specify which customer
    parent_customer_id = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Required if user_type is CUSTOMER_USER"
    )
    
    # New fields for approval workflow (keeping existing email verification)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_users'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.username

class CustomerInvitation(models.Model):
    email = models.EmailField()
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_invitations')
    token = models.CharField(max_length=100, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"Invitation for {self.email} from {self.customer.username}"