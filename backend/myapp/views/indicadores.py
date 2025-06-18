"""Módulo com os ViewSets do Django Rest Framework para indicadores de produção e manutenção."""

from django_filters.rest_framework import DjangoFilterBackend
from myapp.authentication import AppTokenAuthentication
from myapp.filters import EficienciaFilter, PerformanceFilter, RepairFilter
from myapp.models import Eficiencia, Performance, Repair
from myapp.permissions import HomeAccessPermission
from myapp.serializers import EficienciaSerializer, PerformanceSerializer, RepairSerializer
from myapp.views.base import BasicDynamicFieldsViewSets
from rest_framework_simplejwt.authentication import JWTAuthentication


class EficienciaViewSet(BasicDynamicFieldsViewSets):  # cSpell: words eficiencia
    """
    ViewSet para gerenciamento de registros de Eficiência.
    Este ViewSet fornece operações CRUD (Create, Read, Update, Delete) para o modelo Eficiencia.
    Inclui filtragem, autenticação JWT e requer que o usuário esteja autenticado.
    Atributos:
        queryset: Conjunto de dados contendo todos os registros de Eficiencia.
        serializer_class: Classe serializadora para converter objetos Eficiencia em JSON.
        filter_backends: Define DjangoFilterBackend como backend de filtragem.
        filterset_class: Classe que define os campos filtráveis do modelo.
        permission_classes: Define que apenas usuários autenticados podem acessar os endpoints.
        authentication_classes: Utiliza autenticação JWT (JSON Web Token).
    Métodos HTTP suportados:
        - GET: Listar/Recuperar registros de Eficiencia
        - POST: Criar novo registro de Eficiencia
        - PUT/PATCH: Atualizar registro de Eficiencia existente
        - DELETE: Remover registro de Eficiencia
    """

    queryset = Eficiencia.objects.all()  # pylint: disable=E1101
    serializer_class = EficienciaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = EficienciaFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]


class PerformanceViewSet(BasicDynamicFieldsViewSets):
    """
    ViewSet para gerenciamento de registros de Performance.
    Este ViewSet fornece operações CRUD (Create, Read, Update, Delete) para o modelo Performance.
    Inclui filtragem, autenticação JWT e requer que o usuário esteja autenticado.
    Atributos:
        queryset: Conjunto de dados contendo todos os registros de Performance.
        serializer_class: Classe serializadora para converter objetos Performance em JSON.
        filter_backends: Define DjangoFilterBackend como backend de filtragem.
        filterset_class: Classe que define os campos filtráveis do modelo.
        permission_classes: Define que apenas usuários autenticados podem acessar os endpoints.
        authentication_classes: Utiliza autenticação JWT (JSON Web Token).
    Métodos HTTP suportados:
        - GET: Listar/Recuperar registros de Performance
        - POST: Criar novo registro de Performance
        - PUT/PATCH: Atualizar registro de Performance existente
        - DELETE: Remover registro de Performance
    """

    queryset = Performance.objects.all()  # pylint: disable=E1101
    serializer_class = PerformanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PerformanceFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]


class RepairViewSet(BasicDynamicFieldsViewSets):
    """
    ViewSet para gerenciamento de registros de Reparo.
    Este ViewSet fornece operações CRUD (Create, Read, Update, Delete) para o modelo Repair.
    Inclui filtragem, autenticação JWT e requer que o usuário esteja autenticado.
    Atributos:
        queryset: Conjunto de dados contendo todos os registros de Repair.
        serializer_class: Classe serializadora para converter objetos Repair em JSON.
        filter_backends: Define DjangoFilterBackend como backend de filtragem.
        filterset_class: Classe que define os campos filtráveis do modelo.
        permission_classes: Define que apenas usuários autenticados podem acessar os endpoints.
        authentication_classes: Utiliza autenticação JWT (JSON Web Token).
    Métodos HTTP suportados:
        - GET: Listar/Recuperar registros de Repair
        - POST: Criar novo registro de Repair
        - PUT/PATCH: Atualizar registro de Repair existente
        - DELETE: Remover registro de Repair
    """

    queryset = Repair.objects.all()  # pylint: disable=E1101
    serializer_class = RepairSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RepairFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]
