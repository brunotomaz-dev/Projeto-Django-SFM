"""Módulo com as views do Django Rest Framework para produção e qualidade"""

import pandas as pd
from django.db import connections
from django_filters.rest_framework import DjangoFilterBackend
from myapp.authentication import AppTokenAuthentication
from myapp.filters import QualProdFilter
from myapp.models import QualProd
from myapp.permissions import HomeAccessPermission
from myapp.serializers import QualProdSerializer
from myapp.views.base import BasicDynamicFieldsViewSets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


# ================================================================================================ #
#                                      PRODUCTION + QUALIDADE                                      #
# ================================================================================================ #
class QualProdViewSet(BasicDynamicFieldsViewSets):
    """
    ViewSet para gerenciamento de Produtos Qualificados (QualProd).
    Este ViewSet fornece operações CRUD completas para o modelo QualProd,
    com autenticação JWT e permissões de acesso restritas a usuários autenticados.
    Attributes:
        queryset: QuerySet contendo todos os objetos QualProd
        serializer_class: Classe serializadora para conversão de objetos QualProd
        filter_backends: Lista de backends de filtro utilizados
        filterset_class: Classe de filtro personalizada para QualProd
        permission_classes: Classes de permissão requeridas
        authentication_classes: Classes de autenticação utilizadas
    Métodos HTTP suportados:
        - GET: Listar/Recuperar produtos qualificados
        - POST: Criar novo produto qualificado
        - PUT/PATCH: Atualizar produto qualificado existente
        - DELETE: Remover produto qualificado
    """

    # pylint: disable=E1101
    queryset = QualProd.objects.all()
    serializer_class = QualProdSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = QualProdFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]


# ================================================================================================ #
#                                      MAQUINA INFO PRODUCTION                                     #
# ================================================================================================ #
class MaquinaInfoProductionViewSet(APIView):
    """
    Exibe informações de máquinas filtradas por período de tempo.

    Exemplo de uso:
    - GET /maquinainfo/period/?period=2021-01-01,2021-01-31
    """

    def get(self, request):
        """
        Retorna uma lista de dados de máquina filtrada por período de tempo.

        Query parameters:
        - period: período de tempo no formato 'YYYY-MM-DD,YYYY-MM-DD' (obrigatório)

        Resposta:
        - results: lista de dicionários com os dados da máquina
        """
        period = request.query_params.get("period", None)
        if not period:
            return Response(
                {"error": "Period parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        first_day, last_day = self.parse_period(period)
        if not first_day or not last_day:
            return Response(
                {"error": "Invalid period format. Use 'YYYY-MM-DD,YYYY-MM-DD'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = self.build_query(first_day, last_day)

        data = self.execute_query(query)

        return Response(data)

    @action(detail=False, methods=["get"], url_path="by-product", url_name="by_product")
    def by_product(self, request):
        """
        Retorna uma lista de dados de máquina filtrada por período de tempo,
        considerando a troca de produtos dentro do mesmo turno.

        Query parameters:
        - period: período de tempo no formato 'YYYY-MM-DD,YYYY-MM-DD' (obrigatório)

        Resposta:
        - results: lista de dicionários com os dados da máquina separados por produto
        """
        period = request.query_params.get("period", None)
        if not period:
            return Response(
                {"error": "Period parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        first_day, last_day = self.parse_period(period)
        if not first_day or not last_day:
            return Response(
                {"error": "Invalid period format. Use 'YYYY-MM-DD,YYYY-MM-DD'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = self.build_product_query(first_day, last_day)
        data = self.execute_query(query)

        return Response(data)

    def build_product_query(self, first_day, last_day):
        """
        Constrói consulta SQL que considera a troca de produtos dentro do mesmo turno.

        Parâmetros:
        - first_day: data de início do período no formato 'YYYY-MM-DD'
        - last_day: data de fim do período no formato 'YYYY-MM-DD'

        Retorna:
        - query: consulta SQL para obter dados separados por produto
        """
        query = f"""
            SELECT
                linha,
                maquina_id,
                turno,
                produto,
                contagem_total_ciclos as total_ciclos,
                contagem_total_produzido as total_produzido_sensor,
                data_registro
            FROM (
                SELECT
                    (SELECT TOP 1 t2.fabrica FROM AUTOMACAO.dbo.maquina_cadastro t2
                    WHERE t2.maquina_id = t1.maquina_id AND t2.data_registro <= t1.data_registro
                    ORDER BY t2.data_registro DESC, t2.hora_registro DESC) as fabrica,
                    (SELECT TOP 1 t2.linha FROM AUTOMACAO.dbo.maquina_cadastro t2
                    WHERE t2.maquina_id = t1.maquina_id AND t2.data_registro <= t1.data_registro
                    ORDER BY t2.data_registro DESC, t2.hora_registro DESC) as linha,
                    t1.maquina_id,
                    t1.turno,
                    t1.produto,
                    t1.contagem_total_ciclos,
                    t1.contagem_total_produzido,
                    t1.data_registro,
                    t1.hora_registro,
                    ROW_NUMBER() OVER (
                        PARTITION BY t1.data_registro, t1.turno, t1.maquina_id, t1.produto
                        ORDER BY t1.data_registro DESC, t1.hora_registro DESC) AS rn
                FROM AUTOMACAO.dbo.maquina_info t1
            ) AS t
            WHERE t.rn = 1
                AND hora_registro > '00:01'
                AND data_registro between '{first_day}' and '{last_day}'
            ORDER BY data_registro, linha, maquina_id, turno, produto
        """
        return query

    def parse_period(self, period):
        """
        Analisa o período informado e retorna as datas de início e fim do período.

        Parâmetros:
        - period: período a ser analisado no formato 'YYYY-MM-DD,YYYY-MM-DD'

        Retorna:
        - first_day: data de início do período no formato 'YYYY-MM-DD'
        - last_day: data de fim do período no formato 'YYYY-MM-DD'

        Lança ValueError caso o período seja inválido.
        """
        try:
            first_day, last_day = period.split(",")
            first_day = pd.to_datetime(first_day).strftime("%Y-%m-%d")
            last_day = pd.to_datetime(last_day).strftime("%Y-%m-%d")
            return first_day, last_day
        except ValueError:
            return None, None

    def build_query(self, first_day, last_day):
        """
        Constrói as consultas para a API de informações de máquinas filtrada por período de tempo.

        Parâmetros:
        - first_day: data de início do período no formato 'YYYY-MM-DD'
        - last_day: data de fim do período no formato 'YYYY-MM-DD'

        Retorna:
        - query: consulta SQL para obter a lista de dados da máquina
        """
        query = f"""
            SELECT
                linha,
                maquina_id,
                turno,
                contagem_total_ciclos as total_ciclos,
                contagem_total_produzido as total_produzido_sensor,
                produto,
                data_registro
            FROM (
                SELECT
                    (SELECT TOP 1 t2.fabrica FROM AUTOMACAO.dbo.maquina_cadastro t2
                    WHERE t2.maquina_id = t1.maquina_id AND t2.data_registro <= t1.data_registro
                    ORDER BY t2.data_registro DESC, t2.hora_registro DESC) as fabrica,
                    (SELECT TOP 1 t2.linha FROM AUTOMACAO.dbo.maquina_cadastro t2
                    WHERE t2.maquina_id = t1.maquina_id AND t2.data_registro <= t1.data_registro
                    ORDER BY t2.data_registro DESC, t2.hora_registro DESC) as linha,
                    t1.maquina_id,
                    t1.turno,
                    t1.contagem_total_ciclos,
                    t1.contagem_total_produzido,
                    t1.produto,
                    t1.data_registro,
                    t1.hora_registro,
                    ROW_NUMBER() OVER (
                        PARTITION BY t1.data_registro, t1.turno, t1.maquina_id
                        ORDER BY t1.data_registro DESC, t1.hora_registro DESC) AS rn
                FROM AUTOMACAO.dbo.maquina_info t1
            ) AS t
            WHERE t.rn = 1
                AND hora_registro > '00:01'
                AND data_registro between '{first_day}' and '{last_day}'
        """

        return query

    def execute_query(self, query):
        """
        Executes the given query and count query on the database and returns
        a response with the results.

        Args:
            query (str): The query to execute to get the records.
            request (Request): The request object.

        Returns:
            Response: The response containing the results, page, total pages, and total records.
        """
        try:
            with connections["sqlserver"].cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

                if not rows:
                    return Response(
                        [],
                        status=status.HTTP_200_OK,
                    )

                df = pd.DataFrame.from_records(rows, columns=[col[0] for col in cursor.description])

                return df.to_dict("records")
        # pylint: disable=W0718
        except Exception as e:
            print(f"Erro na execução da query: {str(e)}")
            return Response(
                {"error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
