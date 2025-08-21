from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
import uuid
import random
from django.utils import timezone

# Create your models here.
class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    #add profile picture
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ], null=True, blank=True)

    # email must be unique
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    #phone number for otps later
    phone_number = PhoneNumberField(null=False, blank=False, unique=True,region="EG",default="0")
    
    user_type = models.CharField(
        max_length=20, 
        choices=[
            ('CUSTOMER', 'Customer'),
            ('CUSTOMER_USER', 'Customer User')
        ],
        default='CUSTOMER',null=True, blank=True
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
        