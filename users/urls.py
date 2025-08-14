from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    RegisterView, 
    SendInvitationView,
    UserProfileView,
    CustomTokenObtainPairView,
    LogoutView
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User management
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('send-invitation/', SendInvitationView.as_view(), name='send_invitation'),
]