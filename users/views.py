from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
import uuid
from .models import CustomUser, CustomerInvitation
from .serializers import  CustomerInvitationSerializer, RegisterInitSerializer, CompleteRegistrationSerializer
from services.thingboard_services import create_tb_user
import random
from rest_framework import status
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import OTPVerifySerializer
from .serializers import ResetPasswordSerializer
from rest_framework.views import APIView



# OTP functions

def generate_otp(identifier: str, purpose: str):
    """Generate and cache OTP for a specific identifier (phone/email) and purpose"""
    otp = str(random.randint(1000, 9999))  # 6-digit OTP
    cache_key = f"otp_{identifier}"
    cache.set(cache_key, {"otp": otp, "purpose": purpose}, timeout=300)  # 5 minutes
    if settings.DEBUG:
        print(f"[DEBUG OTP] Identifier={identifier}, Purpose={purpose}, OTP={otp}")

    return otp

def verify_otp(identifier: str, otp: str) -> str | None:
    """
    Verify OTP for identifier.
    Returns the purpose (registration/login/reset_password) if valid, else None.
    """
    cache_key = f"otp_{identifier}"
    cached_data = cache.get(cache_key)
    

    if cached_data and cached_data["otp"] == otp:
        cache.delete(cache_key)  # 🔑 Prevent reuse
        return cached_data["purpose"]

    return None



class RegisterInitView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterInitSerializer
   
    def post(self, request):
        phone = request.data.get("phone_number")
        email = request.data.get("email")

        if not phone or not email:
            return Response({"error": "Phone and Email are required"}, status=400)

        otp = generate_otp(email, "registration")  # or phone
        return Response({"message": "OTP sent. Verify to continue."})
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{uidb64}/{token}/"
        print(f"Optional email verification link: {verification_link}")
        

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

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    identifier = request.data.get("email") or request.data.get("phone_number")
    otp_input = request.data.get("otp")

    if not identifier or not otp_input:
        return Response({"error": "Identifier and OTP are required"}, status=400)

    # ✅ Verify OTP against cache
    purpose = verify_otp(identifier, otp_input)

    if not purpose:
        return Response({"error": "Invalid or expired OTP"}, status=400)

    if purpose == "registration":
        # ✅ Mark email/phone as verified (no DB lookup here)
        cache.set(f"verified_{identifier}", True, timeout=600)  # 10 min validity
        return Response({"message": "OTP verified. Proceed to set password."})

    elif purpose == "login":
        return Response({"message": "OTP verified. Login allowed."})

    elif purpose == "reset_password":
        return Response({"message": "OTP verified. Proceed to reset password."})

    return Response({"error": "Invalid purpose"}, status=400)




#reset password
@permission_classes([AllowAny])
class RequestResetPasswordView(APIView):
    def post(self, request):
        identifier = request.data.get("phone_number") or request.data.get("email")
        if not identifier:
            return Response({"error": "Phone or Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if "@" in identifier:
                user = CustomUser.objects.get(email=identifier)
                if not user.email_verified:
                    return Response({"error": "Email not verified. Please verify your email first."}, status=status.HTTP_400_BAD_REQUEST)
                method = "email"
            else:
                user = CustomUser.objects.get(phone_number=identifier)
                method = "phone_number"
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Generate OTP with purpose = password_reset
        generate_otp(
            identifier=identifier,
            purpose="reset_password"
        )

        return Response(
            {"message": f"OTP sent to your {method}. Please verify it to reset your password."},
            status=status.HTTP_200_OK
        )

@permission_classes([AllowAny])
class ResetPasswordView(APIView):
    def post(self, request):
        identifier = request.data.get("phone_number") or request.data.get("email")
        if not identifier:
            return Response({"error": "Phone or Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if "@" in identifier:
                user = CustomUser.objects.get(email=identifier)
                if not user.email_verified:
                    return Response({"error": "Email not verified. Please verify your email first."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # serializer with password + confirm
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user)
            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteRegistrationView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CompleteRegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
    
        phone = validated.get("phone_number")
        email = validated.get("email")
        password = validated.get("password")
        confirm = validated.get("confirm_password")

        if not phone or not email or not password:
            return Response({"error": "Phone, Email, and Password are required"}, status=400)

        if password != confirm:
            return Response({"error": "Passwords do not match"}, status=400)

        # ✅ ensure OTP was verified
        if not cache.get(f"verified_{email}") and not cache.get(f"verified_{phone}"):
            return Response({"error": "OTP not verified"}, status=400)

        # ✅ create user only now (single call!)
        user = CustomUser.objects.create_user(
            username=email,   # or phone if you prefer
            email=email,
            phone_number=phone,
            password=password,
            user_type=validated.get("user_type"),
            parent_customer_id=validated.get("parent_customer_id"),
            is_active=True
        )

        # ✅ create ThingsBoard user
        try:
            # If the request has an invitation token (means user invited by an existing customer)
            invitation_customer_id = request.data.get("invitation_customer_id")
            if invitation_customer_id:
        # User was invited -> create CUSTOMER_USER under that customer
                                        create_tb_user(
            email=user.email,
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            user_type="CUSTOMER_USER",
            parent_customer_id=invitation_customer_id
        )
            else:
                    create_tb_user(
                email=user.email,
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                user_type="CUSTOMER"
            )
        except Exception as e:
            print(f"ThingsBoard user creation failed: {e}")

        return Response({"message": "Registration complete. You can now log in."})
