from django.utils import timezone


class AbsoluteSessionTimeoutMiddleware:
    """
    Enforces an absolute session timeout independent of activity.
    Stores the session start time as an epoch timestamp in the session.
    """

    ABSOLUTE_MINUTES = 10

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session = request.session
        now_ts = timezone.now().timestamp()
        started_ts = session.get("session_started_at")

        if started_ts is None:
            session["session_started_at"] = now_ts
        else:
            elapsed_seconds = now_ts - float(started_ts)
            if elapsed_seconds >= self.ABSOLUTE_MINUTES * 60:
                session.flush()

        response = self.get_response(request)
        return response

