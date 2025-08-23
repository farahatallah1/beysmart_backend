import email
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.utils import timezone
from .models import CustomerInvitation


User = get_user_model()

class RegisterInitSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    phone_number = serializers.CharField(required=True)
    
    # For invitation flow
    invitation_token = serializers.CharField(required=False, allow_blank=True)

    
class CompleteRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(max_length=15, required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    user_type = serializers.ChoiceField(
        choices=[('CUSTOMER', 'Customer'), ('CUSTOMER_USER', 'Customer User')],
        required=False
    )
    parent_customer_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        if attrs.get('user_type') == 'CUSTOMER_USER' and not attrs.get('parent_customer_id'):
            raise serializers.ValidationError({
                "parent_customer_id": "Parent customer ID is required when user_type is CUSTOMER_USER."
            })
        return attrs



   
        
class OTPVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    email = serializers.EmailField(required=False)   # optional
    phone_number = serializers.CharField(max_length=15, required=False)
   

    def validate(self, data):
        if not data.get("email") and not data.get("phone_number"):
            raise serializers.ValidationError("Either email or phone must be provided.")
        return data


         
class CustomerInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerInvitation
        fields = ('email',)


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def save(self, user):
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'birthday', 'gender')
        
    def validate_birthday(self, value):
        """Validate birthday is not in the future"""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Birthday cannot be in the future.")
        return value
