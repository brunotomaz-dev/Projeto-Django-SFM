"""
ViewSet para exibir e editar informações de IHM de máquinas - União de maquina info e maquina ihm.
"""

from django_filters.rest_framework import DjangoFilterBackend
from myapp.authentication import AppTokenAuthentication
from myapp.filters import InfoIHMFilter
from myapp.models import InfoIHM
from myapp.permissions import HomeAccessPermission
from myapp.serializers import InfoIHMSerializer
from myapp.views.base import BasicDynamicFieldsViewSets
from rest_framework_simplejwt.authentication import JWTAuthentication


class InfoIHMViewSet(BasicDynamicFieldsViewSets):
    """
    Exibe e edita informações de IHM de máquinas.

    Exemplo de uso:
    - GET /infoihm/?data_registro=2021-01-01
    - GET /infoihm/?data_registro__gt=2021-01-01
    - GET /infoihm/?data_registro__lt=2021-01-01
    - GET /infoihm/?data_registro__gt=2021-01-01&data_registro__lt=2021-01-31
    """

    # pylint: disable=E1101
    queryset = InfoIHM.objects.all()
    serializer_class = InfoIHMSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = InfoIHMFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]
