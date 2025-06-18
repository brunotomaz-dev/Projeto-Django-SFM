"""Views para interações com o Protheus."""

import pandas as pd
from django.db import connections
from myapp.authentication import AppTokenAuthentication
from myapp.permissions import HomeAccessPermission
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


# ================================================================================================ #
#                                            CÂMARA FRIA                                           #
# ================================================================================================ #
class StockOnCFViewSet(APIView):
    """
    Exibe informações de estoque de produtos em CF.
    """

    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]

    def get(self, _request):
        """
        Retorna uma lista de dados de estoque de produtos em CF.

        Resposta:
        - results: lista de dicionários com os dados de estoque
        """
        query = self.__build_query()

        data = self.execute_query(query)

        return Response(data)

    @staticmethod
    def __build_query():
        """
        Constrói as consultas para a API de informações de estoque de produtos em CF.

        Retorna:
        - query: consulta SQL para obter a lista de dados de estoque
        """
        # cSpell: words QATU LOCPAD totvsdb

        # Select
        select_ = "SELECT SB1.B1_DESC AS produto, SB2.B2_QATU AS quantidade"

        # From
        from_ = "FROM SB2000 SB2 WITH (NOLOCK)"

        # Join
        join_ = """
            INNER JOIN SB1000 SB1 WITH (NOLOCK)
            ON SB1.B1_FILIAL = '01' AND SB1.B1_COD = SB2.B2_COD AND SB1.D_E_L_E_T_<>'*'
            """

        # where
        where_ = """
            WHERE SB2.B2_FILIAL='0101' AND SB2.B2_LOCAL='CF' AND SB1.B1_TIPO='PA'
            AND SB1.B1_LOCPAD='CF' AND SB2.D_E_L_E_T_<>'*' AND SB2.B2_QATU > 0
        """

        # Order By
        order_by_ = "ORDER BY SB2.B2_QATU DESC"

        query = f"{select_} {from_} {join_} {where_} {order_by_}"

        return query

    def execute_query(self, query):
        """
        Executa uma consulta SQL no banco de dados SQL Server.
        Args:
            query (str): Query SQL a ser executada no banco de dados.
        Returns:
            Response ou list:
                - Se a query for bem sucedida: lista de dicionários com os dados
                - Se a query for bem sucedida mas não retornar resultados:
                    Response com lista vazia e status 200
                - Se ocorrer erro: Response com mensagem de erro e status 500
        Raises:
            Exception: Captura qualquer exceção que ocorra durante a execução da query
        """
        try:
            with connections["totvsdb"].cursor() as cursor:
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


class StockStatusViewSet(APIView):
    """
    Exibe informações de estoque de produtos em CF.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, _request):
        """
        Retorna uma lista de dados de estoque de produtos em CF.

        Resposta:
        - results: lista de dicionários com os dados de estoque
        """
        query = self.__build_query()

        data = self.execute_query(query)

        return Response(data)

    @staticmethod
    def __build_query():
        """
        Constrói as consultas para a API de informações de estoque de produtos em CF.

        Retorna:
        - query: consulta SQL para obter a lista de dados de estoque
        """
        # cSpell: words QATU LOCPAD totvsdb usuario codbem

        # Data de hoje
        curr_date = pd.Timestamp.now().strftime("%Y%m%d")

        # Select
        select_ = """SELECT
            B1_DESC AS produto,
            D3_QUANT AS quantidade,
            D3_UM AS unidade,
            D3_EMISSAO AS data,
            CYV_HRRPBG AS hora,
            CYV_CDUSRP AS usuario
        """

        # From
        from_ = "FROM SD3000 SD3 WITH (NOLOCK)"

        # Join
        join_ = """
            LEFT JOIN SB1000 SB1 WITH (NOLOCK) ON B1_FILIAL='01'
            AND B1_COD=D3_COD AND SB1.D_E_L_E_T_<>'*'
            LEFT JOIN CYV000 CYV WITH (NOLOCK) ON CYV_FILIAL=D3_FILIAL
            AND CYV_NRRPET=D3_IDENT AND CYV.D_E_L_E_T_<>'*'
            LEFT JOIN CYB000 CYB WITH (NOLOCK) ON CYB_FILIAL=D3_FILIAL
            AND CYB_CDMQ=CYV_CDMQ AND CYB.D_E_L_E_T_<>'*'
        """

        # where
        where_ = f"""
            WHERE
            D3_FILIAL = '0101'
            AND D3_LOCAL='CF'
            AND B1_TIPO = 'PA'
            AND D3_CF = 'PR0'
            AND D3_ESTORNO <> 'S'
            AND D3_EMISSAO = '{curr_date}'
            AND SD3.D_E_L_E_T_<>'*'
        """

        # Order By
        order_by_ = "ORDER BY D3_EMISSAO DESC, CYV_HRRPBG DESC"

        # Options
        options_ = "OPTION (HASH JOIN, FORCE ORDER)"

        query = f"{select_} {from_} {join_} {where_} {order_by_} {options_}"

        return query

    def execute_query(self, query):
        """
        Executa uma consulta SQL no banco de dados SQL Server.
        Args:
            query (str): Query SQL a ser executada no banco de dados.
        Returns:
            Response ou list:
                - Se a query for bem sucedida: lista de dicionários com os dados
                - Se a query for bem sucedida mas não retornar resultados:
                    Response com lista vazia e status 200
                - Se ocorrer erro: Response com mensagem de erro e status 500
        Raises:
            Exception: Captura qualquer exceção que ocorra durante a execução da query
        """
        try:
            with connections["totvsdb"].cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

                if not rows:
                    return []

                df = pd.DataFrame.from_records(rows, columns=[col[0] for col in cursor.description])

                return df.to_dict("records")
        # pylint: disable=W0718
        except Exception as e:
            print(f"Erro na execução da query: {str(e)}")
            return Response(
                {"error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ================================================================================================ #
#                                       CONTAGEM DE CARRINHOS                                      #
# ================================================================================================ #
class CartCountViewSet(APIView):
    """
    Exibe informações de contagem de carrinhos.

    Exemplo de uso:
    - GET /cart_count/period/?period=2021-01-01,2021-01-31
    """

    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]

    def get(self, request):
        """
        Retorna uma lista de dados de contagem de carrinhos.

        Resposta:
        - results: lista de dicionários com os dados de contagem
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

        query = self.__build_query(first_day, last_day)
        data = self.execute_query(query)

        if isinstance(data, dict) and "error" in data:
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if "error" in data:
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"results": data})

    @staticmethod
    def parse_period(period):
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
            first_day = pd.to_datetime(first_day).strftime("%Y%m%d")
            last_day = pd.to_datetime(last_day).strftime("%Y%m%d")
            return first_day, last_day
        except ValueError:
            return None, None

    @staticmethod
    def __build_query(first_day, last_day):
        """
        Constrói as consultas para a API de informações de contagem de carrinhos.

        Retorna:
        - query: consulta SQL para obter a lista de dados de contagem
        """
        # cSpell: words QATU LOCPAD totvsdb

        # Select
        select_ = "SELECT Data_apontamento, Turno, COUNT(Carrinho) AS Contagem_Carrinhos"

        # From
        from_ = f"""
            FROM (
                SELECT
                    CYV.CYV_CCCA01 as Carrinho,
                    CYV.CYV_DTRPBG as Data_apontamento,
                    CASE
                        WHEN CYV.CYV_HRRPBG >= '00:00:00'
                            AND CYV.CYV_HRRPBG < '08:00:00' THEN 'NOT'
                        WHEN CYV.CYV_HRRPBG >= '08:00:00'
                            AND CYV.CYV_HRRPBG < '16:00:00' THEN 'MAT'
                        WHEN CYV.CYV_HRRPBG >= '16:00:00'
                            AND CYV.CYV_HRRPBG <= '23:59:59' THEN 'VES'
                    END AS Turno
                FROM CYV000 AS CYV (NOLOCK)
                WHERE
                    CYV_FILIAL='0101' AND
                    CYV_DTRPBG BETWEEN {first_day} AND {last_day} AND
                    CYV.CYV_CDMQ like 'ESF%' AND
                    CYV.D_E_L_E_T_<>'*'
            ) AS subquery
        """

        # Group By
        group_by_ = "GROUP BY Data_apontamento, Turno"

        # Order By
        order_by_ = "ORDER BY Data_apontamento DESC, Turno"

        query = f"{select_} {from_} {group_by_} {order_by_}"

        return query

    def execute_query(self, query):
        """
        Executa uma consulta SQL no banco de dados SQL Server.
        Args:
            query (str): Query SQL a ser executada no banco de dados.
        Returns:
            Response ou list:
                - Se a query for bem sucedida: lista de dicionários com os dados
                - Se a query for bem sucedida mas não retornar resultados:
                    Response com lista vazia e status 200
                - Se ocorrer erro: Response com mensagem de erro e status 500
        Raises:
            Exception: Captura qualquer exceção que ocorra durante a execução da query
        """
        try:
            with connections["totvsdb"].cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

                if not rows:
                    return []

                df = pd.DataFrame.from_records(rows, columns=[col[0] for col in cursor.description])

                return df.to_dict("records")
        # pylint: disable=W0718
        except Exception as e:
            print(f"Erro na execução da query: {str(e)}")
            return Response(
                {"error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
