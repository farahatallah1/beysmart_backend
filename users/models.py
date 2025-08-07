from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class CustomUser(AbstractUser):
    age = models.DateField(null=True, blank=True)  
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ], null=True, blank=True)

    # email must be unique
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username