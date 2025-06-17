"""
@brief Módulo que contém as views para exibir e editar informações de IHM - Apontamentos recebidos.
"""

import numpy as np
import pandas as pd
from django_filters.rest_framework import DjangoFilterBackend
from myapp.data_analysis import CleanData
from myapp.filters import MaquinaIHMFilter
from myapp.models import MaquinaIHM
from myapp.serializers import MaquinaIHMSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication


class MaquinaIHMViewSet(viewsets.ModelViewSet):
    """
    Exibe e edita informações de IHM de máquinas.

    Exemplo de uso:
    - GET /maquinaihm/?data_registro=2021-01-01
    - GET /maquinaihm/?data_registro__gt=2021-01-01
    - GET /maquinaihm/?data_registro__lt=2021-01-01
    - GET /maquinaihm/?data_registro__gt=2021-01-01&data_registro__lt=2021-01-31
    """

    # pylint: disable=E1101
    queryset = MaquinaIHM.objects.all()
    serializer_class = MaquinaIHMSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MaquinaIHMFilter
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Converte o queryset em um DataFrame
        df = pd.DataFrame(list(queryset.values()))

        # Realiza a limpeza de dados
        cleaner = CleanData()
        df_cleaned = cleaner.clean_data(df)

        # Cria coluna s_backup
        df_cleaned["s_backup"] = np.where(
            df_cleaned["equipamento"].astype(str).str.isdigit(), df_cleaned["equipamento"], None
        )

        # Remove os valores numéricos da coluna equipamento
        df_cleaned["equipamento"] = np.where(
            df_cleaned["equipamento"].astype(str).str.isdigit(),
            None,
            df_cleaned["equipamento"],
        )

        # Converte o DataFrame em uma um queryset
        cleaned_data = df_cleaned.to_dict("records")

        # Serializa o queryset limpo e retorna a resposta
        serializer = self.get_serializer(cleaned_data, many=True)
        return Response(serializer.data)
