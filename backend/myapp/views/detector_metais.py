"""Módulo de views do Django Rest Framework para Detector de Metais"""

from django_filters.rest_framework import DjangoFilterBackend
from myapp.filters import DetectorMetaisFilter
from myapp.models import DetectorMetais
from myapp.serializers import DetectorMetaisSerializer
from myapp.views.base import BasicDynamicFieldsViewSets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class DetectorMetaisViewSet(BasicDynamicFieldsViewSets):
    """
    ViewSet para gerenciamento de registros de Detector de Metais.
    Este ViewSet fornece operações CRUD (Create, Read, Update, Delete) para o modelo DetectorMetais.
    Inclui filtragem, autenticação JWT e requer que o usuário esteja autenticado.
    """

    queryset = DetectorMetais.objects.all()  # pylint: disable=E1101
    serializer_class = DetectorMetaisSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DetectorMetaisFilter
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
