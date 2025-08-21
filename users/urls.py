from django.urls import path
from .views import verify_email, approve_user, SendInvitationView, RegisterInitView, CompleteRegistrationView
from .views import verify_otp_view
from .views import ResetPasswordView
from .views import RequestResetPasswordView

urlpatterns = [
    path("register/", RegisterInitView.as_view(), name="register"),
    path("verify-email/<uidb64>/<token>/", verify_email, name="verify_email"),
    path("approve-user/<int:user_id>/", approve_user, name="approve_user"),
    path("send-invitation/", SendInvitationView.as_view(), name="send_invitation"),
    path("verify-otp/", verify_otp_view, name="verify_otp"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("request-reset-password/", RequestResetPasswordView.as_view(), name="request_reset_password"),
    path("complete-registeration/", CompleteRegistrationView.as_view(), name="complete_registeration"),
]