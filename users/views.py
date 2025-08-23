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

# Login and Authentication Views
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token


# OTP functions

def generate_otp(identifier: str, purpose: str):
    """Generate and cache OTP for a specific identifier (phone/email) and purpose"""
    otp = str(random.randint(1000, 9999))  # 4-digit OTP
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

        # 🔒 Check if email or phone already exists
        try:
            existing_user = CustomUser.objects.get(email=email)
            return Response({
                "error": "An account with this email already exists. Please use a different email or try logging in.",
                "email_already_exists": True
            }, status=400)
        except CustomUser.DoesNotExist:
            pass

        try:
            existing_user = CustomUser.objects.get(phone_number=phone)
            return Response({
                "error": "An account with this phone number already exists. Please use a different phone number or try logging in.",
                "phone_already_exists": True
            }, status=400)
        except CustomUser.DoesNotExist:
            pass

        # ✅ No duplicates found, generate OTP
        otp = generate_otp(email, "registration")
        return Response({"message": "OTP sent. Verify to continue."})
        

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
        user.email_verified = True  # ✅ Mark email as verified
        user.save()
        print(f"✅ Email verified for user: {user.email}")
        return HttpResponse("<h1>Email verified successfully! You can now log in.</h1>")
    else:
        return HttpResponse("<h1>Invalid verification link or token expired.</h1>", status=400)


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
        # Get user by phone number or email
        try:
            if "@" in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
            
            # Login the user
            login(request, user)
            
            return Response({
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "user_type": user.user_type,
                    "is_approved": user.is_approved,
                    "email_verified": user.email_verified
                }
            })
            
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=400)

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

        # 🔒 CUSTOMER_USER can only register with invitation
        user_type = validated.get("user_type")
        if user_type == 'CUSTOMER_USER':
            invitation_customer_id = request.data.get("invitation_customer_id")
            if not invitation_customer_id:
                return Response({
                    "error": "CUSTOMER_USER registration requires an invitation. Please contact your customer administrator.",
                    "invitation_required": True
                }, status=400)
            
            # Verify the invitation exists and is valid
            try:
                invitation = CustomerInvitation.objects.get(
                    email=email,
                    customer_id=invitation_customer_id,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                print(f"✅ Valid invitation found for {email}")
                
                # Mark invitation as used
                invitation.is_used = True
                invitation.save()
                print(f"✅ Invitation marked as used for {email}")
                
            except CustomerInvitation.DoesNotExist:
                return Response({
                    "error": "Invalid or expired invitation. Please contact your customer administrator.",
                    "invalid_invitation": True
                }, status=400)

        # 🔒 Double-check for duplicates (in case user was created between OTP and completion)
        try:
            existing_user = CustomUser.objects.get(email=email)
            return Response({
                "error": "An account with this email already exists. Please use a different email or try logging in.",
                "email_already_exists": True
            }, status=400)
        except CustomUser.DoesNotExist:
            pass

        try:
            existing_user = CustomUser.objects.get(phone_number=phone)
            return Response({
                "error": "An account with this phone number already exists. Please use a different phone number or try logging in.",
                "phone_already_exists": True
            }, status=400)
        except CustomUser.DoesNotExist:
            pass

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
        
        # ✅ Auto-approve CUSTOMER users, CUSTOMER_USER needs approval
        if user.user_type == 'CUSTOMER':
            user.is_approved = True
            user.save()
            print(f"✅ Auto-approved CUSTOMER user: {user.email}")
        else:
            # CUSTOMER_USER needs approval from parent customer
            user.is_approved = False
            user.save()
            print(f"⏳ CUSTOMER_USER pending approval: {user.email}")
            
            # Send approval request email to parent customer
            try:
                self.send_approval_request_email(user)
                print(f"✅ Approval request sent to parent customer")
            except Exception as e:
                print(f"❌ Approval request failed: {e}")

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

        # ✅ Send verification email after user creation
        try:
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verification_link = f"{settings.FRONTEND_URL}/verify-email/{uidb64}/{token}/"
            
            send_mail(
                "Verify your email - BeySmart App",
                f"Welcome to BeySmart! Please click the following link to verify your email address:\n\n{verification_link}\n\nThis link will expire in 24 hours.\n\nIf you didn't create this account, please ignore this email.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            print(f"✅ Verification email sent to {user.email}")
        except Exception as e:
            print(f"❌ Verification email sending failed: {e}")

        return Response({"message": "Registration complete. Please check your email to verify your account."})

# Login and Authentication Views

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({"error": "Email and password are required"}, status=400)
        
        # Try to authenticate with email
        user = authenticate(username=email, password=password)
        
        if user is None:
            return Response({"error": "Invalid credentials"}, status=400)
        
        if not user.is_active:
            return Response({"error": "Account is deactivated"}, status=400)
        
        # ✅ Check if email is verified (REQUIRED for email login)
        if not user.email_verified:
            return Response({
                "error": "Email not verified. Please verify your email first, or use phone + OTP login.",
                "email_verification_required": True,
                "suggested_login_method": "phone_otp"
            }, status=400)
        
        if not user.is_approved and user.user_type == 'CUSTOMER_USER':
            return Response({"error": "Account pending approval"}, status=400)
        
        # Login the user
        login(request, user)
        
        return Response({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_type": user.user_type,
                "is_approved": user.is_approved,
                "email_verified": user.email_verified
            }
        })

class PhoneOTPLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({"error": "Phone number is required"}, status=400)
        
        try:
            # Check if user exists with this phone number
            user = CustomUser.objects.get(phone_number=phone_number)
            
            if not user.is_active:
                return Response({"error": "Account is deactivated"}, status=400)
            
            # Only require approval for CUSTOMER_USER, not for CUSTOMER
            if user.user_type == 'CUSTOMER_USER' and not user.is_approved:
                return Response({"error": "Account pending approval"}, status=400)
            
            # Generate OTP for phone login
            otp = generate_otp(phone_number, "login")
            
            return Response({
                "message": "OTP sent to your phone number. Please verify to continue."
            })
            
        except CustomUser.DoesNotExist:
            return Response({"error": "No account found with this phone number"}, status=400)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"})

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": str(user.phone_number),
            "profile_picture": user.profile_picture.url if user.profile_picture else None,
            "birthday": user.birthday,
            "gender": user.gender,
            "user_type": user.user_type,
            "parent_customer_id": user.parent_customer_id,
            "is_approved": user.is_approved,
            "email_verified": user.email_verified,
            "date_joined": user.date_joined,
            "last_login": user.last_login
        })
    
    def put(self, request):
        user = request.user
        data = request.data
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'birthday' in data:
            user.birthday = data['birthday']
        if 'gender' in data:
            user.gender = data['gender']
        
        user.save()
        
        return Response({"message": "Profile updated successfully"})

class CheckAuthView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            "authenticated": True,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
                "user_type": request.user.user_type,
                "is_approved": request.user.is_approved
            }
        })

class CheckAccountExistsView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        
        if not email and not phone_number:
            return Response({"error": "Email or phone number is required"}, status=400)
        
        exists = {}
        
        if email:
            try:
                CustomUser.objects.get(email=email)
                exists['email'] = True
            except CustomUser.DoesNotExist:
                exists['email'] = False
        
        if phone_number:
            try:
                CustomUser.objects.get(phone_number=phone_number)
                exists['phone_number'] = True
            except CustomUser.DoesNotExist:
                exists['phone_number'] = False
        
        return Response({
            "exists": exists,
            "message": "Account existence checked successfully"
        })
