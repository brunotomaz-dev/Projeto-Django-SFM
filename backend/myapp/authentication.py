from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


# Flake8: noqa
class AppTokenAuthentication(BaseAuthentication):
    """
    Autenticação personalizada que verifica tanto tokens JWT quanto o token fixo da aplicação.
    Primeiro verifica se é o token da aplicação, e se não for, tenta a autenticação JWT.
    """

    def authenticate(self, request):
        # Obter o token do cabeçalho Authorization
        auth_header = request.META.get("HTTP_AUTHORIZATION")

        if not auth_header:
            return None

        # Extrair o token (removendo 'Bearer ' se presente)
        try:
            auth_parts = auth_header.split()
            if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
                return None

            token = auth_parts[1]
        except (ValueError, AttributeError):
            return None

        # Verificar se é o token da aplicação HOME_APP_TOKEN
        if token == settings.HOME_APP_TOKEN:
            # Cria um usuário anônimo com flag especial
            user = AnonymousUser()
            user.is_home_app = True
            return (user, None)

        # Se não for o token da aplicação, tenta autenticar com JWT
        jwt_auth = JWTAuthentication()
        try:
            return jwt_auth.authenticate(request)
        except AuthenticationFailed:
            # Se falhar a autenticação JWT e não for o token da aplicação, retorna None
            return None
