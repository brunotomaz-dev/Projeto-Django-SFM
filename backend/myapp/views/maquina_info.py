"""
@brief Módulo que contém as views para exibir e editar informações de máquinas.
"""

import logging

import pandas as pd
from django_filters.rest_framework import DjangoFilterBackend
from myapp.authentication import AppTokenAuthentication
from myapp.filters import MaquinaInfoFilter
from myapp.models import MaquinaInfo
from myapp.permissions import HomeAccessPermission
from myapp.serializers import MaquinaInfoHourSerializer, MaquinaInfoSerializer
from myapp.views.base import BasicDynamicFieldsViewSets
from myapp.views_processor import ProductionDataProcessor
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

# Configuração do logger
logger = logging.getLogger(__name__)


class MaquinaInfoViewSet(BasicDynamicFieldsViewSets):
    """
    Exibe e edita informações de máquinas.

    Exemplo de uso:
    - GET /maquinainfo/?data_registro=2021-01-01
    - GET /maquinainfo/?data_registro__gt=2021-01-01
    - GET /maquinainfo/?data_registro__lt=2021-01-01
    - GET /maquinainfo/?data_registro__gt=2021-01-01&data_registro__lt=2021-01-31
    """

    # pylint: disable=E1101
    queryset = MaquinaInfo.objects.all()
    serializer_class = MaquinaInfoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MaquinaInfoFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]


class MaqInfoHourProductionViewSet(viewsets.ModelViewSet):
    """
    Exibe e edita informações de produção por hora.

    Exemplo de uso:
    - GET /maq_info_hour_prod/?data_registro=2021-01-01
    - GET /maq_info_hour_prod/?data_registro__gt=2021-01-01
    - GET /maq_info_hour_prod/?data_registro__lt=2021-01-01
    - GET /maq_info_hour_prod/?data_registro__gt=2021-01-01&data_registro__lt=2021-01-31
    """

    # pylint: disable=E1101
    queryset = MaquinaInfo.objects.all()
    serializer_class = MaquinaInfoHourSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MaquinaInfoFilter
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            # Se o queryset estiver vazio, retorne uma lista vazia com status 200
            if not queryset.exists():
                return Response([], status=status.HTTP_200_OK)

            # Converte o queryset em um DataFrame
            df = pd.DataFrame(list(queryset.values()))

            # Se o DataFrame estiver vazio, retorne lista vazia com status 200
            if df.empty:
                return Response([], status=status.HTTP_200_OK)

            # Logger
            logger.info("Processando %d registros de produção", len(df))

            # Instancia o processador de dados de produção
            processor = ProductionDataProcessor()

            # Processa os dados
            processed_data = processor.process_production_data(df)

            # Logger de sucesso
            logger.debug("Dados processados com sucesso")

            # Converte o DataFrame em uma um queryset
            df = processed_data.to_dict("records")

            # Serializa o queryset limpo e retorna a resposta
            serializer = self.get_serializer(df, many=True)
            return Response(serializer.data)
        except Exception as e:  # pylint: disable=W0718
            logger.error("Erro ao processar dados: %s", str(e))
            return Response(
                {"error": f"Erro ao processar dados: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
