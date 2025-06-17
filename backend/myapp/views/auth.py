"""Authentication and registration views for the application."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from ..serializers import CustomTokenObtainPairSerializer, RegisterSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    View para alteração de senha do usuário.
    Requer autenticação JWT.

    Parâmetros:
    - old_password: senha atual
    - new_password: nova senha
    """
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not user.check_password(old_password):
        return Response({"detail": "Senha atual incorreta"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"detail": "Senha alterada com sucesso"})


class CustomTokenObtainPairView(TokenObtainPairView):
    """Serializador de token"""

    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    Registra um novo usuário no sistema.
    """

    serializer_class = RegisterSerializer
