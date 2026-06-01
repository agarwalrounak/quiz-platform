from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RegisterSerializer,
    RoleTokenObtainPairSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Public self-registration (creates a `user` role account)."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    """Obtain a JWT pair; response includes role + the user object."""

    serializer_class = RoleTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    """Returns the currently authenticated user."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
