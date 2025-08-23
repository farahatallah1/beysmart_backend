from django.urls import path
from .views import verify_email, approve_user, SendInvitationView, RegisterInitView, CompleteRegistrationView
from .views import verify_otp_view
from .views import ResetPasswordView
from .views import RequestResetPasswordView
from .views import LoginView, LogoutView, UserProfileView, CheckAuthView, PhoneOTPLoginView, CheckAccountExistsView

urlpatterns = [
    path("register/", RegisterInitView.as_view(), name="register"),
    path("verify-email/<uidb64>/<token>/", verify_email, name="verify_email"),
    path("approve-user/<int:user_id>/", approve_user, name="approve_user"),
    path("send-invitation/", SendInvitationView.as_view(), name="send_invitation"),
    path("verify-otp/", verify_otp_view, name="verify_otp"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("request-reset-password/", RequestResetPasswordView.as_view(), name="request_reset_password"),
    path("complete-registeration/", CompleteRegistrationView.as_view(), name="complete_registeration"),
    path("login/", LoginView.as_view(), name="login"),
    path("phone-login/", PhoneOTPLoginView.as_view(), name="phone_login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("check-auth/", CheckAuthView.as_view(), name="check_auth"),
    path("check-account-exists/", CheckAccountExistsView.as_view(), name="check_account_exists"),
]