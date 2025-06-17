"""Módulo de Views do Django Rest Framework para manipulação de ausências e presenças"""

from django_filters.rest_framework import DjangoFilterBackend
from myapp.authentication import AppTokenAuthentication
from myapp.filters import AbsenceLogFilter, PresenceLogFilter
from myapp.models import AbsenceLog, PresenceLog
from myapp.permissions import HomeAccessPermission
from myapp.serializers import AbsenceLogSerializer, PresenceLogSerializer
from myapp.views.base import BasicDynamicFieldsViewSets
from rest_framework import viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication


# ================================================================================================ #
#                                            ABSENTEÍSMO                                           #
# ================================================================================================ #
class AbsenceViewSet(BasicDynamicFieldsViewSets):
    """
    Um ViewSet para manipulação de operações de registro de ausências na API.
    Este ViewSet fornece operações CRUD para objetos AbsenceLog através de uma interface REST API.
    Requer autenticação JWT e o usuário deve estar autenticado para acessar os endpoints.
    Atributos:
        queryset: QuerySet com todos os objetos AbsenceLog
        serializer_class: Classe serializadora para o modelo AbsenceLog
        filter_backends: Lista de backends de filtro utilizados
        filter_class: Classe de filtro para filtragem de AbsenceLog
        permission_classes: Lista de classes de permissão requeridas
        authentication_classes: Lista de classes de autenticação utilizadas
    """

    queryset = AbsenceLog.objects.all()  # pylint: disable=E1101
    serializer_class = AbsenceLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AbsenceLogFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]


# ================================================================================================ #
#                                             PRESENÇAS                                            #
# ================================================================================================ #
class PresenceLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de registros de Presença.
    Este ViewSet fornece operações CRUD (Create, Read, Update, Delete) para o modelo PresenceLog.
    Inclui filtragem, autenticação JWT e requer que o usuário esteja autenticado.
    Atributos:
        queryset: Conjunto de dados contendo todos os registros de PresenceLog.
        serializer_class: Classe serializadora para converter objetos PresenceLog em JSON.
        filter_backends: Define DjangoFilterBackend como backend de filtragem.
        filterset_class: Classe que define os campos filtráveis do modelo.
        permission_classes: Define que apenas usuários autenticados podem acessar os endpoints.
        authentication_classes: Utiliza autenticação JWT (JSON Web Token).
    Métodos HTTP suportados:
        - GET: Listar/Recuperar registros de PresenceLog
        - POST: Criar novo registro de PresenceLog
        - PUT/PATCH: Atualizar registro de PresenceLog existente
        - DELETE: Remover registro de PresenceLog
    """

    queryset = PresenceLog.objects.all()  # pylint: disable=E1101
    serializer_class = PresenceLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PresenceLogFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]
