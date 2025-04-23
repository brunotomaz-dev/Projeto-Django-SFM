"""Módulo de visualizações do Django Rest Framework"""

import logging
import traceback

import numpy as np
import pandas as pd
from django.core.cache import cache
from django.db import connections

# from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView

from .authentication import AppTokenAuthentication
from .data_analysis import CleanData
from .filters import (
    AbsenceLogFilter,
    ActionPlanFilter,
    EficienciaFilter,
    InfoIHMFilter,
    MaquinaIHMFilter,
    MaquinaInfoFilter,
    PerformanceFilter,
    PresenceLogFilter,
    QualidadeIHMFilter,
    QualProdFilter,
    RepairFilter,
    ServiceOrderFilter,
    ServiceRequestFilter,
)
from .models import (
    AbsenceLog,
    ActionPlan,
    Eficiencia,
    InfoIHM,
    MaquinaIHM,
    MaquinaInfo,
    Performance,
    PresenceLog,
    QualidadeIHM,
    QualProd,
    Repair,
    ServiceOrder,
    ServiceRequest,
)
from .permissions import HomeAccessPermission
from .serializers import (
    AbsenceLogSerializer,
    ActionPlanSerializer,
    CustomTokenObtainPairSerializer,
    EficienciaSerializer,
    InfoIHMSerializer,
    MaquinaIHMSerializer,
    MaquinaInfoHourSerializer,
    MaquinaInfoSerializer,
    PerformanceSerializer,
    PresenceLogSerializer,
    QualidadeIHMSerializer,
    QualProdSerializer,
    RegisterSerializer,
    RepairSerializer,
    ServiceOrderSerializer,
    ServiceRequestSerializer,
)
from .views_processor import ProductionDataProcessor, QualidadeDataProcessor

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    View para alteração de senha do usuário.
    Requer autenticação JWT.

    Parâmetros:
    - old_password: senha atual
    - new_password: nova senha
    """
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not user.check_password(old_password):
        return Response({"detail": "Senha atual incorreta"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"detail": "Senha alterada com sucesso"})


class CustomTokenObtainPairView(TokenObtainPairView):
    """Serializador de token"""

    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    Registra um novo usuário no sistema.
    """

    serializer_class = RegisterSerializer


class BasicDynamicFieldsViewSets(viewsets.ModelViewSet):
    """ViewSet básico com suporte a campos dinâmicos"""

    def get_serializer(self, *args, **kwargs):
        # Recupera os campos dinâmicos da query string
        fields = self.request.query_params.get("fields", None)

        # Se houver campos dinâmicos, passa-os para o serializador
        kwargs["fields"] = fields.split(",") if fields else None

        return super().get_serializer(*args, **kwargs)


class ReadOnlyDynamicFieldsViewSets(viewsets.ReadOnlyModelViewSet):
    """ViewSet somente leitura com suporte a campos dinâmicos"""

    def get_serializer(self, *args, **kwargs):
        # Recupera os campos dinâmicos da query string
        fields = self.request.query_params.get("fields", None)

        # Se houver campos dinâmicos, passa-os para o serializador
        kwargs["fields"] = fields.split(",") if fields else None

        return super().get_serializer(*args, **kwargs)


# ================================================================================================ #
#                                           MAQUINA INFO                                           #
# ================================================================================================ #
# Create your views here.
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

            # Converte o queryset em um DataFrame
            df = pd.DataFrame(list(queryset.values()))

            # Logger
            logger.info("Processando %d registros de produção", len(df))

            # Instancia o processador de dados de produção
            processor = ProductionDataProcessor()

            # Processa os dados
            processed_data = processor.process_production_data(df)

            # Logger de sucesso
            logger.debug("Dados processados com sucesso")

            # Converte o DataFrame em um queryset
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


# ================================================================================================ #
#                                            MÁQUINA IHM                                           #
# ================================================================================================ #
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


# ================================================================================================ #
#                                             INFO IHM                                             #
# ================================================================================================ #
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


# ================================================================================================ #
#                                             QUALIDADE                                            #
# ================================================================================================ #
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

            # Converte o queryset em um DataFrame
            df = pd.DataFrame(list(queryset.values()))

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
            logger.error("Erro ao processar dados: %s", str(e))
            return Response(
                {"error": f"Erro ao processar dados: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
#                                            INDICADORES                                           #
# ================================================================================================ #
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


# ================================================================================================ #
#                                            ABSENTEÍSMO                                           #
# ================================================================================================ #
class AbsenceViewSet(BasicDynamicFieldsViewSets):
    """
    Um ViewSet para manipulação de operações de registro de ausências na API.
    Este ViewSet fornece operações CRUD para objetos AbsenceLog através de uma interface REST API.
    Requer autenticação JWT e o usuário deve estar autenticado para acessar os endpoints.
    Atributos:
        queryset: QuerySet com todos os objetos AbsenceLog
        serializer_class: Classe serializadora para o modelo AbsenceLog
        filter_backends: Lista de backends de filtro utilizados
        filter_class: Classe de filtro para filtragem de AbsenceLog
        permission_classes: Lista de classes de permissão requeridas
        authentication_classes: Lista de classes de autenticação utilizadas
    """

    queryset = AbsenceLog.objects.all()  # pylint: disable=E1101
    serializer_class = AbsenceLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AbsenceLogFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]


# ================================================================================================ #
#                                             PRESENÇAS                                            #
# ================================================================================================ #
class PresenceLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de registros de Presença.
    Este ViewSet fornece operações CRUD (Create, Read, Update, Delete) para o modelo PresenceLog.
    Inclui filtragem, autenticação JWT e requer que o usuário esteja autenticado.
    Atributos:
        queryset: Conjunto de dados contendo todos os registros de PresenceLog.
        serializer_class: Classe serializadora para converter objetos PresenceLog em JSON.
        filter_backends: Define DjangoFilterBackend como backend de filtragem.
        filterset_class: Classe que define os campos filtráveis do modelo.
        permission_classes: Define que apenas usuários autenticados podem acessar os endpoints.
        authentication_classes: Utiliza autenticação JWT (JSON Web Token).
    Métodos HTTP suportados:
        - GET: Listar/Recuperar registros de PresenceLog
        - POST: Criar novo registro de PresenceLog
        - PUT/PATCH: Atualizar registro de PresenceLog existente
        - DELETE: Remover registro de PresenceLog
    """

    queryset = PresenceLog.objects.all()  # pylint: disable=E1101
    serializer_class = PresenceLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PresenceLogFilter
    permission_classes = [HomeAccessPermission]
    authentication_classes = [AppTokenAuthentication, JWTAuthentication]


# ================================================================================================ #
#                                            ACTION PLAN                                           #
# ================================================================================================ #
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


# ================================================================================================ #
#                                              MANUSIS                                             #
# ================================================================================================ #
class ServiceOrderViewSet(ReadOnlyDynamicFieldsViewSets):
    """
    ViewSet para lidar com ordens de serviço.

    Este ViewSet executa uma query personalizada com JOIN, mantendo suporte
    a filtros e campos dinâmicos.
    """

    queryset = ServiceOrder.objects.all()  # pylint: disable=E1101
    serializer_class = ServiceOrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ServiceOrderFilter
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def _get_cache_key(self, request):
        """Gera uma chave de cache baseada nos parâmetros da requisição."""
        cache_params = request.query_params.copy()
        return f"service_orders:{hash(frozenset(cache_params.items()))}"

    def _add_date_filter(self, param_name, field_name, where_clauses, params, request):
        """
        Adiciona um filtro de data maior ou igual, ajustando para o fuso horário brasileiro (UTC-3).

        Parâmetros:
        - param_name: Nome do parâmetro na URL (ex: 'data_criacao__gt')
        - field_name: Nome do campo no banco de dados (ex: 'mo.created_at')
        - where_clauses: Lista de cláusulas WHERE
        - params: Lista de parâmetros para a query
        - request: Objeto de requisição
        """
        if param_name in request.query_params:
            param_value = request.query_params.get(param_name)
            if param_value:
                # Ajusta para o timezone brasileiro (UTC-3)
                where_clauses.append(
                    f"({field_name} AT TIME ZONE 'UTC' "
                    f"AT TIME ZONE 'America/Sao_Paulo')::date >= %s::date"
                )
                params.append(param_value)

        # Filtro para data_criacao__lt (menor ou igual)
        # Adicionamos esta condição para completude dos filtros
        if "data_criacao__lt" in request.query_params:
            param_value = request.query_params.get("data_criacao__lt")
            where_clauses.append(
                f"({field_name} AT TIME ZONE 'UTC' "
                f"AT TIME ZONE 'America/Sao_Paulo')::date <= %s::date"
            )
            params.append(param_value)

        return where_clauses, params

    def _add_date_equal_filter(self, param_name, field_name, where_clauses, params, request):
        """
        Adiciona um filtro de data igual, considerando o dia completo no fuso horário brasileiro.

        Para um filtro de igualdade em datas, precisamos considerar que a data é armazenada com
        timezone UTC, mas queremos filtrar pelo dia local (UTC-3).
        """
        if param_name in request.query_params:
            param_value = request.query_params.get(param_name)

            if param_name == "inicio_atendimento":
                if param_value:
                    where_clauses.append(
                        f"(({field_name} AT TIME ZONE 'UTC' "
                        f"AT TIME ZONE 'America/Sao_Paulo')::date = %s::date "
                        f"OR (mo.maint_finished_at AT TIME ZONE 'UTC' "  # Corrigido
                        f"AT TIME ZONE 'America/Sao_Paulo')::date = %s::date "
                        # f"OR (mo.updated_at AT TIME ZONE 'UTC' "  # Corrigido
                        # f"AT TIME ZONE 'America/Sao_Paulo')::date = %s::date)"
                    )
                    # Precisa adicionar o mesmo valor três vezes, uma para cada condição
                    params.append(param_value)
                    params.append(param_value)
                    params.append(param_value)
            else:
                if param_value:
                    # Para DATE(X) = Y, precisamos considerar que o dia em UTC pode ser
                    where_clauses.append(
                        f"({field_name} AT TIME ZONE 'UTC' "
                        f"AT TIME ZONE 'America/Sao_Paulo')::date = %s::date"
                    )
                    params.append(param_value)
        return where_clauses, params

    def _add_equality_filter(self, param_name, field_name, where_clauses, params, request):
        """Adiciona um filtro de igualdade se o parâmetro estiver presente."""
        if param_name in request.query_params:
            param_value = request.query_params.get(param_name)
            if param_value:
                where_clauses.append(f"{field_name} = %s")
                params.append(param_value)
        return where_clauses, params

    def _build_filter_clauses(self, request):
        """Constrói as cláusulas de filtro com base nos parâmetros da requisição."""
        where_clauses = []
        params = []

        # Filtro para data_criacao (igualdade - filtro por dia específico no timezone local)
        self._add_date_equal_filter("data_criacao", "mo.created_at", where_clauses, params, request)
        self._add_date_equal_filter(
            "data_conclusao", "mo.closed_at", where_clauses, params, request
        )
        self._add_date_equal_filter(
            "inicio_atendimento", "mo.maint_started_at", where_clauses, params, request
        )

        # Filtro para data_criacao__gt (maior ou igual)
        self._add_date_filter(
            "data_criacao__gt", "DATE(mo.created_at)", where_clauses, params, request
        )

        # Outros filtros existentes
        self._add_equality_filter(
            "status_id", "mo.maint_order_status_id", where_clauses, params, request
        )

        self._add_equality_filter("numero_os", "mo.order_number", where_clauses, params, request)

        return where_clauses, params

    def _process_query_results(self, cursor, results):
        """Processa os resultados da query e retorna como uma lista de dicionários."""
        columns = [col[0] for col in cursor.description]
        data = []
        for row in results:
            item = {}
            for i, col in enumerate(columns):
                item[col] = row[i]
            data.append(item)
        return data

    def _get_cached_response(self, request):
        """Tenta obter e retornar dados do cache."""
        cache_key = self._get_cache_key(request)
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        return None

    def _build_complete_query(self, request):
        """Constrói a query completa com filtros e ordenação."""
        # Construa a query base
        query = self.__build_query()

        # Adicione filtros
        where_clauses, params = self._build_filter_clauses(request)
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        # Adicione ordenação e limite
        query += " ORDER BY mo.created_at DESC LIMIT 100"

        return query, params

    def _execute_query_and_cache(self, query, params, request):
        """Executa a query e armazena os resultados no cache."""
        with connections["postgres"].cursor() as cursor:
            # Execute a query
            cursor.execute(query, params)

            # Verifique se há resultados válidos
            if cursor.description is None:
                return Response([])

            results = cursor.fetchall()
            if not results:
                return Response([])

            # Processe os resultados
            data = self._process_query_results(cursor, results)

            # Armazene no cache
            cache_key = self._get_cache_key(request)
            cache.set(cache_key, data, 300)

            return Response(data)

    def _handle_query_error(self, e):
        """Lida com os erros de execução da query."""

        traceback_str = traceback.format_exc()
        print(f"Erro detalhado:\n{traceback_str}")
        return Response(
            {"error": f"Database error: {str(e)}", "traceback": traceback_str},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def list(self, request, *args, **kwargs):
        """Implementação otimizada com cache de plano e resultados."""
        # Tente obter do cache primeiro
        cached_response = self._get_cached_response(request)
        if cached_response:
            return cached_response

        # Construa a query completa
        query, params = self._build_complete_query(request)

        try:
            # Execute a query e cache os resultados
            return self._execute_query_and_cache(query, params, request)
        except Exception as e:  # pylint: disable=W0718
            return self._handle_query_error(e)

    def __build_query(self):
        """
        Constrói a consulta SQL personalizada para obter as ordens de serviço.

        Retorna:
            str: Consulta SQL personalizada
        """

        # cSpell: words codigo localizacao descricao nivel matype matnat maint manutencao
        # cSpell: words secundario criacao responsavel worktime historico servico reqs

        # Select
        select_ = """
            SELECT
                mo.id,
                mo.order_number AS numero_os,
                l1.code AS codigo_localizacao_nivel1,
                l1.description AS descricao_localizacao_nivel1,
                l2.code AS codigo_localizacao_nivel2,
                l2.description AS descricao_localizacao_nivel2,
                l3.code AS codigo_localizacao_nivel3,
                l3.description AS descricao_localizacao_nivel3,
                ass.code as codigo_ativo,
                ass.description AS ativo,
                matype.description AS tipo_manutencao,
                matnat.description as natureza_manutencao,
                mo.maint_req_id AS numero_ss,
                ss.requestor AS solicitante_ss,
                mst.description AS assunto_principal,
                mst1.description AS assunto_secundario,
                mo.description AS descricao,
                mo.maint_order_status_id as status_id,
                st.description AS status,
                mo.priority AS prioridade,
                mo.priority_calculated AS prioridade_calculada,
                mo.created_at AS data_criacao,
                mo.user_text AS criado_por,
                ep.name AS responsavel_manutencao,
                mo.maint_started_at AS inicio_atendimento,
                mo.maint_finished_at AS fim_atendimento,
                mo.performed_worktime AS tempo_trabalho_realizado,
                mo.estimated_worktime AS tempo_estimado_trabalho,
                mo.closed_at AS data_conclusao,
                mo.executed_service_historic AS historico_servico_executado
        """

        # From
        from_ = "FROM maint_orders AS mo"

        # Join
        join_ = """
            JOIN areas AS ar
                ON mo.area_id = ar.id
            LEFT JOIN locations AS l1
                ON mo.first_loc_id = l1.id
            LEFT JOIN locations AS l2
                ON mo.second_loc_id = l2.id
            LEFT JOIN locations AS l3
                ON mo.third_loc_id = l3.id
            LEFT JOIN assets AS ass
                ON mo.asset_id = ass.id
            JOIN maint_service_type_translations AS matype
                ON mo.maint_service_type_id = matype.maint_service_type_id
                AND matype.locale = 'pt-BR'
            JOIN maint_service_nature_translations AS matnat
                ON mo.maint_service_nature_id = matnat.maint_service_nature_id
                AND matype.locale = 'pt-BR'
            LEFT JOIN employees AS ep
                ON mo.employee_id = ep.id
            JOIN maint_order_status_translations AS st
                ON mo.maint_order_status_id = st.maint_order_status_id
                AND st.locale = 'pt-BR'
            LEFT JOIN maint_reqs AS ss
                ON mo.maint_req_id = ss.id
            LEFT JOIN maint_subject_translations AS mst
                ON ss.maint_subject_id = mst.maint_subject_id
                AND mst.locale = 'pt-BR'
            LEFT JOIN maint_subject_translations AS mst1
                ON ss.maint_subject_child_id = mst1.maint_subject_id
                AND mst1.locale = 'pt-BR'
        """

        query = select_ + from_ + join_

        return query

    def get_serializer(self, *args, **kwargs):
        """
        Sobrescreve o método get_serializer para permitir selecionar campos específicos,
        incluindo os que foram adicionados pelos JOINs.
        """
        # Recupera os campos dinâmicos da query string
        fields = self.request.query_params.get("fields", None)

        # Se houver campos dinâmicos, passa-os para o serializador
        kwargs["fields"] = fields.split(",") if fields else None

        return super().get_serializer(*args, **kwargs)


class ServiceRequestViewSet(ReadOnlyDynamicFieldsViewSets):
    """
    ViewSet para lidar com requisições de serviço.

    Este ViewSet executa uma query personalizada com JOIN, mantendo suporte
    a filtros e campos dinâmicos.
    """

    queryset = ServiceRequest.objects.all()  # pylint: disable=E1101
    serializer_class = ServiceRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ServiceRequestFilter
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def _get_cache_key(self, request):
        """Gera uma chave de cache baseada nos parâmetros da requisição."""
        cache_params = request.query_params.copy()
        return f"service_requests:{hash(frozenset(cache_params.items()))}"

    def _add_date_filter(self, param_name, field_name, where_clauses, params, request):
        """
        Adiciona um filtro de data maior ou igual, ajustando para o fuso horário brasileiro (UTC-3).

        Parâmetros:
        - param_name: Nome do parâmetro na URL (ex: 'data_criacao__gt')
        - field_name: Nome do campo no banco de dados (ex: 'mo.created_at')
        - where_clauses: Lista de cláusulas WHERE
        - params: Lista de parâmetros para a query
        - request: Objeto de requisição
        """
        if param_name in request.query_params:
            param_value = request.query_params.get(param_name)
            if param_value:
                # Ajusta para o timezone brasileiro (UTC-3)
                where_clauses.append(
                    f"({field_name} AT TIME ZONE 'UTC' "
                    f"AT TIME ZONE 'America/Sao_Paulo')::date >= %s::date"
                )
                params.append(param_value)

        # Filtro para data_criacao__lt (menor ou igual)
        # Adicionamos esta condição para completude dos filtros
        if "data_criacao__lt" in request.query_params:
            param_value = request.query_params.get("data_criacao__lt")
            where_clauses.append(
                f"({field_name} AT TIME ZONE 'UTC' "
                f"AT TIME ZONE 'America/Sao_Paulo')::date <= %s::date"
            )
            params.append(param_value)

        return where_clauses, params

    def _add_date_equal_filter(self, param_name, field_name, where_clauses, params, request):
        """
        Adiciona um filtro de data igual, considerando o dia completo no fuso horário brasileiro.

        Para um filtro de igualdade em datas, precisamos considerar que a data é armazenada com
        timezone UTC, mas queremos filtrar pelo dia local (UTC-3).
        """
        if param_name in request.query_params:
            param_value = request.query_params.get(param_name)
            if param_value:
                # Para DATE(X) = Y, precisamos considerar que o dia em UTC pode ser
                where_clauses.append(
                    f"({field_name} AT TIME ZONE 'UTC' "
                    f"AT TIME ZONE 'America/Sao_Paulo')::date = %s::date"
                )
                params.append(param_value)
        return where_clauses, params

    def _add_equality_filter(self, param_name, field_name, where_clauses, params, request):
        """Adiciona um filtro de igualdade se o parâmetro estiver presente."""
        if param_name in request.query_params:
            param_value = request.query_params.get(param_name)
            if param_value:
                where_clauses.append(f"{field_name} = %s")
                params.append(param_value)
        return where_clauses, params

    def _build_filter_clauses(self, request):
        """Constrói as cláusulas de filtro com base nos parâmetros da requisição."""
        where_clauses = []
        params = []

        # Filtro para data_criacao (igualdade - filtro por dia específico no timezone local)
        self._add_date_equal_filter("data_criacao", "ss.created_at", where_clauses, params, request)

        # Filtro para data_criacao__gt (maior ou igual)
        self._add_date_filter(
            "data_criacao__gt", "DATE(ss.created_at)", where_clauses, params, request
        )

        # Outros filtros existentes
        self._add_equality_filter(
            "status_id", "ss.maint_req_status_id", where_clauses, params, request
        )

        self._add_equality_filter("numero_ss", "ss.req_number", where_clauses, params, request)

        return where_clauses, params

    def _process_query_results(self, cursor, results):
        """Processa os resultados da query e retorna como uma lista de dicionários."""
        columns = [col[0] for col in cursor.description]
        data = []
        for row in results:
            item = {}
            for i, col in enumerate(columns):
                item[col] = row[i]
            data.append(item)
        return data

    def _get_cached_response(self, request):
        """Tenta obter e retornar dados do cache."""
        cache_key = self._get_cache_key(request)
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        return None

    def _build_complete_query(self, request):
        """Constrói a query completa com filtros e ordenação."""
        # Construa a query base
        query = self.__build_query()

        # Adicione filtros
        where_clauses, params = self._build_filter_clauses(request)
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        # Adicione ordenação e limite
        query += " ORDER BY ss.created_at DESC LIMIT 100"

        return query, params

    def _execute_query_and_cache(self, query, params, request):
        """Executa a query e armazena os resultados no cache."""
        with connections["postgres"].cursor() as cursor:
            # Execute a query
            cursor.execute(query, params)

            # Verifique se há resultados válidos
            if cursor.description is None:
                return Response([])

            results = cursor.fetchall()
            if not results:
                return Response([])

            # Processe os resultados
            data = self._process_query_results(cursor, results)

            # Armazene no cache
            cache_key = self._get_cache_key(request)
            cache.set(cache_key, data, 300)

            return Response(data)

    def _handle_query_error(self, e):
        """Lida com os erros de execução da query."""
        traceback_str = traceback.format_exc()
        print(f"Erro detalhado:\n{traceback_str}")
        return Response(
            {"error": f"Database error: {str(e)}", "traceback": traceback_str},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def list(self, request, *args, **kwargs):
        """Implementação otimizada com cache de plano e resultados."""
        # Tente obter do cache primeiro
        cached_response = self._get_cached_response(request)
        if cached_response:
            return cached_response

        # Construa a query completa
        query, params = self._build_complete_query(request)

        try:
            # Execute a query e cache os resultados
            return self._execute_query_and_cache(query, params, request)
        except Exception as e:  # pylint: disable=W0718
            return self._handle_query_error(e)

    def __build_query(self):
        """
        Constrói a consulta SQL personalizada para obter as requisições de serviço.

        Retorna:
            str: Consulta SQL personalizada
        """

        # cSpell: words classificacao secundario solicitacao seguranca

        # Select
        select_ = """
            SELECT
                ss.id
                , ss.requestor as solicitante
                , mst.description as assunto_principal
                , mst1.description as assunto_secundario
                , ss.solicitation as solicitacao
                , ss.maint_req_status_id as status_id
                , rs.description as status
                , l1.code AS codigo_localizacao_nivel1
                , l1.description AS descricao_localizacao_nivel1
                , l2.code AS codigo_localizacao_nivel2
                , l2.description AS descricao_localizacao_nivel2
                , l3.code AS codigo_localizacao_nivel3
                , l3.description AS descricao_localizacao_nivel3
                , ass.code as codigo_ativo
                , ass.description AS ativo
                , ss.classification as classificacao
                , ss.created_at as data_criacao
                , ss.req_number as numero_ss
                , ss.is_asset_stopped as maquina_esta_parada
                , ss.is_security_item as item_de_seguranca
            """

        # From
        from_ = "FROM maint_reqs as ss"

        # Join
        join_ = """
            LEFT JOIN maint_subject_translations AS mst
                ON ss.maint_subject_id = mst.maint_subject_id
                AND mst.locale = 'pt-BR'
            LEFT JOIN maint_subject_translations AS mst1
                ON ss.maint_subject_child_id = mst1.maint_subject_id
                AND mst1.locale = 'pt-BR'
            LEFT JOIN maint_req_status_translations AS rs
                ON ss.maint_req_status_id = rs.maint_req_status_id
                AND rs.locale = 'pt-BR'
            LEFT JOIN locations AS l1
                ON ss.first_loc_id = l1.id
            LEFT JOIN locations AS l2
                ON ss.second_loc_id = l2.id
            LEFT JOIN locations AS l3
                ON ss.third_loc_id = l3.id
            LEFT JOIN assets AS ass
                ON ss.asset_id = ass.id
        """

        return select_ + from_ + join_

    def get_serializer(self, *args, **kwargs):
        """
        Sobrescreve o método get_serializer para permitir selecionar campos específicos,
        incluindo os que foram adicionados pelos JOINs.
        """
        # Recupera os campos dinâmicos da query string
        fields = self.request.query_params.get("fields", None)

        # Se houver campos dinâmicos, passa-os para o serializador
        kwargs["fields"] = fields.split(",") if fields else None

        return super().get_serializer(*args, **kwargs)
