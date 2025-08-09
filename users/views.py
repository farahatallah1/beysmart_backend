from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import CustomUser
from .serializers import RegisterSerializer
from services.thingboard_services import create_tb_user

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]  # Public endpoint

    def perform_create(self, serializer):
        # Save user in PostgreSQL
        user = serializer.save()

        # Create same user in ThingsBoard
        try:
            create_tb_user(
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                password=self.request.data.get("password")
            )
        except Exception as e:
            # Optional: log the error instead of breaking registration
            print(f"ThingsBoard user creation failed: {e}")
