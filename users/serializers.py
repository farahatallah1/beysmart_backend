from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.utils import timezone
from .models import CustomerInvitation

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
 
    user_type = serializers.ChoiceField(
        choices=[('CUSTOMER', 'Customer'), ('CUSTOMER_USER', 'Customer User')],
        required=True
    )
    parent_customer_id = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Required if user_type is CUSTOMER_USER"
    )
    
    # For invitation flow
    invitation_token = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password", "confirm_password", "birthday", "gender", "user_type", "parent_customer_id", "invitation_token")

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        
        # If user_type is CUSTOMER_USER, parent_customer_id is required
        if attrs.get('user_type') == 'CUSTOMER_USER' and not attrs.get('parent_customer_id'):
            raise serializers.ValidationError({
                "parent_customer_id": "Parent customer ID is required when user_type is CUSTOMER_USER."
            })
        
        return attrs

    def create(self, validated_data):
        invitation_token = validated_data.pop('invitation_token', None)
        
        # Handle invitation flow
        if invitation_token:
            try:
                invitation = CustomerInvitation.objects.get(
                    token=invitation_token,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                # Auto-fill customer info from invitation
                validated_data['user_type'] = 'CUSTOMER_USER'
                validated_data['parent_customer_id'] = str(invitation.customer.id)
                invitation.is_used = True
                invitation.save()
            except CustomerInvitation.DoesNotExist:
                raise serializers.ValidationError("Invalid or expired invitation token.")
        
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False  # prevent login until email verified
        user.save()
        
        # If customer user, they need approval
        if validated_data.get('user_type') == 'CUSTOMER_USER':
            user.is_approved = False
        else:
            user.is_approved = True  # Customers are auto-approved
        
        return user

class CustomerInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerInvitation
        fields = ('email',)