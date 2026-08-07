"""Test-only URL conf for unsafe authenticated endpoints."""
from django.urls import path
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class EchoUnsafeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"ok": True})


urlpatterns = [
    path("api/test/echo-unsafe/", EchoUnsafeView.as_view(), name="echo_unsafe"),
]
