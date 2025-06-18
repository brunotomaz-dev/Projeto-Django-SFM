"""ViewSet para gerenciamento de Planos de Ação"""

from django_filters.rest_framework import DjangoFilterBackend
from myapp.filters import ActionPlanFilter
from myapp.models import ActionPlan
from myapp.serializers import ActionPlanSerializer
from myapp.views.base import BasicDynamicFieldsViewSets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class ActionPlanViewSet(BasicDynamicFieldsViewSets):
    """
    ViewSet para gerenciamento de registros de Planos de Ação.
    Este ViewSet fornece operações CRUD (Create, Read, Update, Delete) para o modelo ActionPlan.
    Inclui filtragem, autenticação JWT e requer que o usuário esteja autenticado.
    Atributos:
        queryset: Conjunto de dados contendo todos os registros de ActionPlan.
        serializer_class: Classe serializadora para converter objetos ActionPlan em JSON.
        filter_backends: Define DjangoFilterBackend como backend de filtragem.
        filterset_class: Classe que define os campos filtráveis do modelo.
        permission_classes: Define que apenas usuários autenticados podem acessar os endpoints.
        authentication_classes: Utiliza autenticação JWT (JSON Web Token).
        Métodos HTTP suportados:
        - GET: Listar/Recuperar registros de ActionPlan
        - POST: Criar novo registro de ActionPlan
        - PUT/PATCH: Atualizar registro de ActionPlan existente
        - DELETE: Remover registro de ActionPlan
    """

    queryset = ActionPlan.objects.all()  # pylint: disable=E1101
    serializer_class = ActionPlanSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ActionPlanFilter
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
