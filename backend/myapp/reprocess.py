"""Módulo para reprocessamento de indicadores"""

import logging

import pandas as pd
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reprocess_indicators(request):
    """
    Reprocessa os indicadores para uma data específica após alterações em InfoIHM

    Exemplo de uso:
    POST /api/reprocess_indicators/
    {
        "data_registro": "2023-05-15"
    }
    """
    try:
        # Importamos aqui para evitar importação circular
        from .schedulers import create_indicators

        data = request.data.get("data_registro")

        if not data:
            return Response({"error": "A data é obrigatória"}, status=status.HTTP_400_BAD_REQUEST)

        # Converter para formato ISO se não estiver
        data = pd.to_datetime(data).strftime("%Y-%m-%d")

        create_indicators(data)
        return Response(
            {"success": f"Indicadores reprocessados para {data}"}, status=status.HTTP_200_OK
        )

    except Exception as e:  # pylint: disable=W0718
        logger.error("Erro ao reprocessar indicadores: %s", str(e))
        return Response(
            {"error": f"Erro ao reprocessar indicadores: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reprocess_full(request):
    """
    Reprocessa os indicadores para uma data específica após alterações em InfoIHM

    Exemplo de uso:
    POST /api/reprocess_full/
    {
        "data_registro": "2023-05-15"
    }
    """
    try:
        # Importamos aqui para evitar importação circular
        from .schedulers import analisar_dados, create_indicators, create_production_data

        data = request.data.get("data_registro")

        if not data:
            return Response({"error": "A data é obrigatória"}, status=status.HTTP_400_BAD_REQUEST)

        # Converter para formato ISO se não estiver
        data = pd.to_datetime(data).strftime("%Y-%m-%d")

        create_indicators(data)
        create_production_data(data)
        analisar_dados(data)
        return Response(
            {"success": f"Reprocessamento completo para {data}"}, status=status.HTTP_200_OK
        )

    except Exception as e:  # pylint: disable=W0718
        logger.error("Erro ao reprocessar: %s", str(e))
        return Response(
            {"error": f"Erro ao reprocessar: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
