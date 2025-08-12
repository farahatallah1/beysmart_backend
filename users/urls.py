from django.contrib import admin
from django.urls import path, include
from users.views import verify_email, approve_user, SendInvitationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("verify-email/<uidb64>/<token>/", verify_email, name="verify_email"),
    path("approve-user/<int:user_id>/", approve_user, name="approve_user"),
    path("send-invitation/", SendInvitationView.as_view(), name="send_invitation"),
]