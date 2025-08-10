from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings

from .models import CustomUser
from .serializers import RegisterSerializer
from services.thingboard_services import create_tb_user


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
                last_name=user.last_name
            )
        except Exception as e:
            print(f"ThingsBoard user creation failed: {e}")

        return HttpResponse("<h1>Email verified successfully! You can now log in.</h1>")
    else:
        return HttpResponse("<h1>Invalid or expired verification link.</h1>", status=400)
