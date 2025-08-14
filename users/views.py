from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate
import uuid

from .models import CustomUser, CustomerInvitation
from .serializers import (
    RegisterSerializer, 
    CustomerInvitationSerializer, 
    UserProfileSerializer,
    CustomTokenObtainPairSerializer
)
from services.thingboard_services import create_tb_user
from services.thingsboard_auth import tb_auth


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{uidb64}/{token}/"

        try:
            send_mail(
                "Verify your email",
                f"Click the link to verify your account: {verification_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
            # For development, don't raise the exception - just log it
            # In production, you might want to handle this differently
            print(f"User created but email verification failed. Verification link: {verification_link}")

        # ADDITIONAL: Send approval request if customer user
        if user.user_type == 'CUSTOMER_USER' and user.parent_customer_id:
            self.send_approval_request_email(user)

    def send_approval_request_email(self, user):
        # Send email to customer asking for approval
        try:
            customer = CustomUser.objects.get(id=user.parent_customer_id)
            
            approval_link = f"{settings.FRONTEND_URL}/approve-user/{user.id}/"
            
            try:
                send_mail(
                    "New User Approval Request",
                    f"A new user {user.first_name} {user.last_name} ({user.email}) has requested to join your customer account. Click here to approve: {approval_link}",
                    settings.DEFAULT_FROM_EMAIL,
                    [customer.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Approval email sending failed: {e}")
        except CustomUser.DoesNotExist:
            print(f"Customer with ID {user.parent_customer_id} not found")


class SendInvitationView(generics.CreateAPIView):
    serializer_class = CustomerInvitationSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        invitation = serializer.save(customer=self.request.user)
        
        # Generate unique token
        invitation.token = str(uuid.uuid4())
        invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
        invitation.save()
        
        # Send invitation email
        invitation_link = f"{settings.FRONTEND_URL}/register?invitation={invitation.token}"
        
        try:
            send_mail(
                "You're invited to join our platform",
                f"You've been invited by {self.request.user.first_name} {self.request.user.last_name} to join their customer account. Click here to register: {invitation_link}",
                settings.DEFAULT_FROM_EMAIL,
                [invitation.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Invitation email sending failed: {e}")


def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        # Create user in ThingsBoard
        try:
            create_tb_user(
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                user_type=user.user_type,
                parent_customer_id=user.parent_customer_id
            )
        except Exception as e:
            print(f"ThingsBoard user creation failed: {e}")

        return HttpResponse("<h1>Email verified successfully! You can now log in.</h1>")
    else:
        return HttpResponse("<h1>Invalid or expired verification link.</h1>", status=400)


def approve_user(request, user_id):
    try:
        user = CustomUser.objects.get(pk=user_id)
        customer = CustomUser.objects.get(id=user.parent_customer_id)
        
        # Check if the current user is the customer
        if request.user != customer:
            return HttpResponse("<h1>Unauthorized</h1>", status=403)
        
        # Approve the user
        user.is_approved = True
        user.approved_by = customer
        user.approved_at = timezone.now()
        user.save()
        
        # Send activation email to approved user (using your existing email system)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{uidb64}/{token}/"
        
        try:
            send_mail(
                "Your account has been approved",
                f"Your account has been approved by {customer.first_name} {customer.last_name}. Click here to activate: {verification_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Approval email sending failed: {e}")
        
        return HttpResponse("<h1>User approved successfully!</h1>")
    except CustomUser.DoesNotExist:
        return HttpResponse("<h1>User not found</h1>", status=404)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that returns JWT tokens with user info"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                'error': 'Invalid credentials',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = serializer.user
        
        # Check if user is active and approved
        if not user.is_active:
            return Response({
                'error': 'Account not activated',
                'detail': 'Please verify your email first'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_approved:
            return Response({
                'error': 'Account not approved',
                'detail': 'Your account is pending approval'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verify user exists in ThingsBoard
        try:
            tb_verification = tb_auth.verify_user_access(user.email, user.user_type)
            
            if not tb_verification['verified']:
                # Log the issue but don't block login for now
                print(f"ThingsBoard verification failed for {user.email}: {tb_verification['message']}")
                
                # Optionally create user in ThingsBoard if missing
                try:
                    if tb_verification.get('tb_data') is None:
                        print(f"Creating missing ThingsBoard user for {user.email}")
                        tb_auth.create_thingsboard_user(
                            email=user.email,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            user_type=user.user_type,
                            parent_customer_id=user.parent_customer_id
                        )
                        print(f"Successfully created ThingsBoard user for {user.email}")
                except Exception as e:
                    print(f"Failed to create ThingsBoard user: {e}")
                
        except Exception as e:
            print(f"ThingsBoard verification error for {user.email}: {e}")
            # Continue with login even if ThingsBoard check fails
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'is_approved': user.is_approved,
            }
        })


class LogoutView(APIView):
    """Logout view that blacklists the refresh token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View to get and update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user