from rest_framework.permissions import BasePermission


class HomeAccessPermission(BasePermission):
    """
    Permite acesso se o usuário estiver autenticado normalmente
    OU se for o token específico da aplicação para a Home
    """

    def has_permission(self, request, view):
        # Usuário autenticado normalmente pode fazer qualquer operação
        if request.user.is_authenticated:
            return True

        # Para token da aplicação, permitir apenas operações de leitura (GET, HEAD, OPTIONS)
        if getattr(request.user, "is_home_app", False):
            return request.method in ["GET", "HEAD", "OPTIONS"]

        return False
