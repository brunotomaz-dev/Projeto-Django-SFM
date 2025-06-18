"""Módulo de views do Django Rest Framework para qualidade recebido de ihm de máquinas"""

import logging

import pandas as pd
from django_filters.rest_framework import DjangoFilterBackend
from myapp.filters import QualidadeIHMFilter
from myapp.models import QualidadeIHM
from myapp.serializers import QualidadeIHMSerializer
from myapp.views_processor import QualidadeDataProcessor
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


class QualidadeIHMViewSet(viewsets.ModelViewSet):
    """
    Exibe e edita informações de qualidade de IHM de máquinas.

    Cálculos realizados:
    1. Bandejas vazias = (peso_total - PESO_SACO) / PESO_BANDEJAS
    2. Bandejas retrabalho = (peso_total - PESO_SACO) / PESO_BANDEJAS

    Constantes utilizadas:
    - PESO_SACO: Peso do saco vazio
    - PESO_BANDEJAS: Peso médio das bandejas

    Arredondamentos:
    - Valores intermediários: 3 casas decimais
    - Quantidade de bandejas: número inteiro

    Exemplo de uso:
    - GET /qualidadeihm/?data_registro=2021-01-01
    - GET /qualidadeihm/?data_registro__gt=2021-01-01
    - GET /qualidadeihm/?data_registro__lt=2021-01-01
    - GET /qualidadeihm/?data_registro__gt=2021-01-01&data_registro__lt=2021-01-31
    """

    # pylint: disable=E1101
    queryset = QualidadeIHM.objects.all()
    serializer_class = QualidadeIHMSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = QualidadeIHMFilter
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
            logger.info("Processando %d registros de qualidade", len(df))

            # Instancia o processador de dados de qualidade
            processor = QualidadeDataProcessor()

            # Processa os dados
            processed_data = processor.process_qualidade_data(df)

            # Logger de sucesso
            logger.debug("Dados processados com sucesso")

            # Converte o DataFrame em uma um queryset
            df = processed_data.to_dict("records")

            # Serializa o queryset limpo e retorna a resposta
            serializer = self.get_serializer(df, many=True)
            return Response(serializer.data)
        except Exception as e:  # pylint: disable=W0718
            # Apenas log e retorno de erro 500 para erros reais de processamento
            logger.error("Erro ao processar dados: %s", str(e))
            return Response(
                {"error": f"Erro ao processar dados: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="raw", url_name="raw_data")
    def raw_data(self, request, *args, **kwargs):  # pylint: disable=W0613
        """
        Retorna os dados originais sem processamento.

        Este endpoint permite acessar os dados brutos do banco de dados,
        antes de qualquer transformação ou cálculo aplicado pelo processador.

        Exemplo de uso:
        - GET /qualidade_ihm/raw/?data_registro=2021-01-01
        """
        try:
            # Aplicar os mesmos filtros da lista normal
            queryset = self.filter_queryset(self.get_queryset())

            # Se o queryset estiver vazio, retorne uma lista vazia
            if not queryset.exists():
                return Response([], status=status.HTTP_200_OK)

            # Serializa os dados originais diretamente, sem processamento adicional
            serializer = self.get_serializer(queryset, many=True)

            # Log informativo
            logger.info("Retornando %d registros de qualidade RAW", queryset.count())

            return Response(serializer.data)

        except Exception as e:  # pylint: disable=W0718
            # Log e tratamento de erros
            logger.error("Erro ao obter dados brutos: %s", str(e))
            return Response(
                {"error": f"Erro ao obter dados brutos: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
