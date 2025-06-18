"""Módulo de visualizações do Django Rest Framework"""

import logging
import traceback

from django.core.cache import cache
from django.db import connections
from django_filters.rest_framework import DjangoFilterBackend
from myapp.filters import ServiceOrderFilter, ServiceRequestFilter
from myapp.models import ServiceOrder, ServiceRequest
from myapp.serializers import ServiceOrderSerializer, ServiceRequestSerializer
from myapp.views.base import ReadOnlyDynamicFieldsViewSets
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


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
        - field_name: Nome do campo no banco de dados (ex: 'os.created_at')
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
                        f"OR (os.maint_finished_at AT TIME ZONE 'UTC' "  # Corrigido
                        f"AT TIME ZONE 'America/Sao_Paulo')::date = %s::date)"
                        # f"OR (os.updated_at AT TIME ZONE 'UTC' "  # Corrigido
                        # f"AT TIME ZONE 'America/Sao_Paulo')::date = %s::date)"
                    )
                    # Precisa adicionar o mesmo valor três vezes, uma para cada condição
                    params.append(param_value)
                    params.append(param_value)
                    # params.append(param_value)
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
        self._add_date_equal_filter("data_criacao", "os.created_at", where_clauses, params, request)
        self._add_date_equal_filter(
            "data_conclusao", "os.closed_at", where_clauses, params, request
        )
        self._add_date_equal_filter(
            "inicio_atendimento", "os.maint_started_at", where_clauses, params, request
        )

        # Filtro para data_criacao__gt (maior ou igual)
        self._add_date_filter(
            "data_criacao__gt", "DATE(os.created_at)", where_clauses, params, request
        )

        # Outros filtros existentes
        self._add_equality_filter(
            "status_id", "os.maint_order_status_id", where_clauses, params, request
        )

        self._add_equality_filter("numero_os", "os.order_number", where_clauses, params, request)

        self._add_equality_filter(
            "tipo_manutencao", "os.maint_service_type_id", where_clauses, params, request
        )

        self._add_equality_filter("cod_ativo", "ass.code", where_clauses, params, request)

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
        query += " ORDER BY os.created_at DESC LIMIT 1000"

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
                os.id,
                os.order_number AS numero_os,
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
                os.maint_req_id AS numero_ss,
                ss.requestor AS solicitante_ss,
                mst.description AS assunto_principal,
                mst1.description AS assunto_secundario,
                os.description AS descricao,
                os.maint_order_status_id as status_id,
                st.description AS status,
                os.priority AS prioridade,
                os.priority_calculated AS prioridade_calculada,
                os.created_at AS data_criacao,
                os.user_text AS criado_por,
                ep.name AS responsavel_manutencao,
                os.maint_started_at AS inicio_atendimento,
                os.maint_finished_at AS fim_atendimento,
                os.performed_worktime AS tempo_trabalho_realizado,
                os.estimated_worktime AS tempo_estimado_trabalho,
                os.closed_at AS data_conclusao,
                os.executed_service_historic AS historico_servico_executado
        """

        # From
        from_ = "FROM maint_orders AS os"

        # Join
        join_ = """
            LEFT JOIN locations AS l1
                ON os.first_loc_id = l1.id
            LEFT JOIN locations AS l2
                ON os.second_loc_id = l2.id
            LEFT JOIN locations AS l3
                ON os.third_loc_id = l3.id
            LEFT JOIN assets AS ass
                ON os.asset_id = ass.id
            LEFT JOIN maint_service_type_translations AS matype
                ON os.maint_service_type_id = matype.maint_service_type_id
                AND matype.locale = 'pt-BR'
            LEFT JOIN maint_service_nature_translations AS matnat
                ON os.maint_service_nature_id = matnat.maint_service_nature_id
                AND matnat.locale = 'pt-BR'
            LEFT JOIN employees AS ep
                ON os.employee_id = ep.id
            LEFT JOIN maint_order_status_translations AS st
                ON os.maint_order_status_id = st.maint_order_status_id
                AND st.locale = 'pt-BR'
            LEFT JOIN maint_reqs AS ss
                ON os.maint_req_id = ss.id
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
        - field_name: Nome do campo no banco de dados (ex: 'os.created_at')
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
        query += " ORDER BY ss.created_at DESC LIMIT 1000"

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


class AssetsPreventiveViewSet(ReadOnlyDynamicFieldsViewSets):
    """
    ViewSet para visualizar as requisições de manutenção preventiva de ativos.
    """

    queryset = ServiceRequest.objects.all()  # pylint: disable=E1101
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def __build_query(self):
        """
        Constrói a consulta SQL personalizada para obter os ativos de manutenção preventiva.

        Retorna:
            str: Consulta SQL personalizada
        """

        # cSpell: words codigo localizacao descricao nivel matype matnat maint manutencao
        # cSpell: words secundario criacao responsavel worktime historico servico reqs

        # Select
        # query = """
        #     SELECT DISTINCT
        #         ass.code as codigo_ativo,
        #         ass.description AS ativo
        #     FROM maint_orders AS mo
        #     LEFT JOIN assets AS ass
        #         ON mo.asset_id = ass.id
        #     WHERE mo.maint_service_type_id in (1, 6) AND mo.maint_order_status_id = 3
        #         AND mo.description LIKE ('PREV%') OR mo.description LIKE ('PINSP%')
        #     ORDER BY ass.description LIMIT 1000
        #     """

        # NOTE: Esta consulta foi feita para corrigir erros até acerto de corretiva pontual
        # cSpell: words guilhermoni goncalves
        query = """
        SELECT DISTINCT
            ass.code as codigo_ativo,
            ass.description AS ativo
        FROM maint_orders AS mo
        LEFT JOIN assets AS ass
            ON mo.asset_id = ass.id
        LEFT JOIN employees AS ep
            ON mo.employee_id = ep.id
        WHERE (mo.maint_service_type_id = 1
                AND (mo.description LIKE ('PREV%') OR mo.description LIKE ('PINSP%'))
            OR (mo.maint_service_type_id = 6
                AND (mo.user_text LIKE ('%GUILHERMONI%') OR ep.name LIKE ('%GONCALVES%'))))
            AND mo.maint_order_status_id = 3
        ORDER BY ass.description LIMIT 1000
        """

        return query

    def __process_query_results(self, cursor, results):
        """Processa os resultados da query e retorna como uma lista de dicionários."""
        columns = [col[0] for col in cursor.description]
        data = []
        for row in results:
            item = {}
            for i, col in enumerate(columns):
                item[col] = row[i]
            data.append(item)
        return data

    def __execute_query(self, query):
        """
        Executa a consulta SQL personalizada e retorna os resultados.
        """
        with connections["postgres"].cursor() as cursor:
            cursor.execute(query)

            # Verifique se há resultados válidos
            if cursor.description is None:
                return Response([])

            results = cursor.fetchall()
            if not results:
                return Response([])

            # Processe os resultados
            data = self.__process_query_results(cursor, results)

            return Response(data)

    def list(self, request, *args, **kwargs):
        """
        Lida com a solicitação GET para listar os ativos de manutenção preventiva.
        """
        query = self.__build_query()
        return self.__execute_query(query)

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
