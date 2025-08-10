from django.urls import path
from .views import RegisterView, verify_email

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/<uidb64>/<token>/", verify_email, name="verify_email"),
]
