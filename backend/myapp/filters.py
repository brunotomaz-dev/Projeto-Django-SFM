"""Módulo com os filtros do Django Rest Framework"""

# cSpell: words conclusao criacao

import django_filters

from .models import (
    AbsenceLog,
    ActionPlan,
    DetectorMetais,
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


class MaquinaInfoFilter(django_filters.FilterSet):
    """Filtro de informações de máquina"""

    data_registro = django_filters.DateFilter(field_name="data_registro")
    maquina_id = django_filters.CharFilter(method="filter_maquina_id")

    def filter_maquina_id(self, queryset, _name, value):
        """
        Filter queryset based on machine IDs.
        This method filters the queryset by the 'maquina_id' field. It accepts both
        single ID values and comma-separated lists of IDs.
        Parameters:
            queryset (QuerySet): The Django queryset to filter
            _name (str): The name of the filter (not used in this method)
            value (str): The machine ID(s) to filter by. Can be a single ID or
                         multiple IDs separated by commas.
        Returns:
            QuerySet: Filtered queryset containing only objects with the specified machine ID(s)
        """

        if "," in value:  # Se contém vírgula, é uma lista
            maquina_ids = value.split(",")
            return queryset.filter(maquina_id__in=maquina_ids)
        return queryset.filter(maquina_id=value)

    class Meta:
        """Classe de metadados"""

        model = MaquinaInfo
        fields = {
            "data_registro": ["exact", "gt", "lt", "gte", "lte"],
            "turno": ["exact"],
            # "maquina_id": ["exact"],
            "status": ["exact"],
        }


class MaquinaIHMFilter(django_filters.FilterSet):
    """Filtro de informações de IHM de máquina"""

    data_registro = django_filters.DateFilter(field_name="data_registro")
    linha = django_filters.CharFilter(lookup_expr="exact")

    class Meta:
        """Classe de metadados"""

        model = MaquinaIHM
        fields = {
            "data_registro": ["exact", "gt", "lt", "gte", "lte"],
            "linha": ["exact"],
        }


class InfoIHMFilter(django_filters.FilterSet):
    """Filtro de informações de máquina"""

    data_registro = django_filters.DateFilter(field_name="data_registro")
    maquina_id = django_filters.CharFilter(method="filter_maquina_id")

    def filter_maquina_id(self, queryset, _name, value):
        """
        Filter queryset based on machine IDs.
        This method filters the queryset by the 'maquina_id' field. It accepts both
        single ID values and comma-separated lists of IDs.
        Parameters:
            queryset (QuerySet): The Django queryset to filter
            _name (str): The name of the filter (not used in this method)
            value (str): The machine ID(s) to filter by. Can be a single ID or
                         multiple IDs separated by commas.
        Returns:
            QuerySet: Filtered queryset containing only objects with the specified machine ID(s)
        """

        if "," in value:  # Se contém vírgula, é uma lista
            maquina_ids = value.split(",")
            return queryset.filter(maquina_id__in=maquina_ids)
        return queryset.filter(maquina_id=value)

    class Meta:
        """Classe de metadados"""

        model = InfoIHM
        fields = {
            "data_registro": ["exact", "gt", "lt", "gte", "lte"],
            # "maquina_id": ["exact"],
            "linha": ["exact"],
            "turno": ["exact"],
        }


class QualidadeIHMFilter(django_filters.FilterSet):
    """Filtro de informações de máquina"""

    data_registro = django_filters.DateFilter(field_name="data_registro")

    class Meta:
        """Classe de metadados"""

        model = QualidadeIHM
        fields = {"data_registro": ["exact", "gt", "lt", "gte", "lte"]}


class QualProdFilter(django_filters.FilterSet):
    """Filtro de informações de máquina"""

    data_registro = django_filters.DateFilter(field_name="data_registro")

    class Meta:
        """Classe de metadados"""

        model = QualProd
        fields = {"data_registro": ["exact", "gt", "lt", "gte", "lte"]}


class EficienciaFilter(django_filters.FilterSet):  # cSpell:ignore Eficiencia
    """Filtro da eficiência"""

    data_registro = django_filters.DateFilter(field_name="data_registro")

    class Meta:
        """Classe de metadados"""

        model = Eficiencia
        fields = {"data_registro": ["exact", "gt", "lt", "gte", "lte"]}


class PerformanceFilter(django_filters.FilterSet):
    """Filtro da eficiência"""

    data_registro = django_filters.DateFilter(field_name="data_registro")

    class Meta:
        """Classe de metadados"""

        model = Performance
        fields = {"data_registro": ["exact", "gt", "lt", "gte", "lte"]}


class RepairFilter(django_filters.FilterSet):
    """Filtro da eficiência"""

    data_registro = django_filters.DateFilter(field_name="data_registro")

    class Meta:
        """Classe de metadados"""

        model = Repair
        fields = {"data_registro": ["exact", "gt", "lt", "gte", "lte"]}


class AbsenceLogFilter(django_filters.FilterSet):
    """Filtro para registros de absenteísmo"""

    data_registro = django_filters.DateFilter(field_name="data_registro")
    data_occ = django_filters.DateFilter(field_name="data_occ")
    data_retorno = django_filters.DateFilter(field_name="data_retorno")
    nome = django_filters.CharFilter(lookup_expr="icontains")
    tipo = django_filters.CharFilter(lookup_expr="exact")
    setor = django_filters.CharFilter(lookup_expr="exact")

    class Meta:
        """Classe de metadados"""

        model = AbsenceLog
        fields = {
            "data_registro": ["exact", "gt", "lt", "gte", "lte"],
            "nome": ["exact", "icontains"],
            "tipo": ["exact"],
            "setor": ["exact"],
            "data_occ": ["exact", "gt", "lt", "gte", "lte"],
            "data_retorno": ["exact", "gt", "lt", "gte", "lte"],
        }


class PresenceLogFilter(django_filters.FilterSet):
    """Filtro para registros de presença"""

    data_registro = django_filters.DateFilter(field_name="data_registro")

    class Meta:
        """Classe de metadados"""

        model = PresenceLog
        fields = {
            "data_registro": ["exact", "gt", "lt", "gte", "lte"],
        }


class ActionPlanFilter(django_filters.FilterSet):
    """Filtro para registros de plano de ação"""

    data_registro = django_filters.DateFilter(field_name="data_registro")
    # Substitui o filtro atual por um método personalizado
    conclusao = django_filters.CharFilter(method="filter_conclusao")

    def filter_conclusao(self, queryset, _name, value):
        """
        Filtra o queryset baseado nos valores de conclusão fornecidos.
        Permite valores únicos ou múltiplos separados por vírgula.
        """
        if "," in value:  # Se contém vírgula, é uma lista de valores
            conclusao_values = [int(v.strip()) for v in value.split(",")]
            return queryset.filter(conclusao__in=conclusao_values)
        # Caso contrário, é um único valor
        return queryset.filter(conclusao=int(value))

    class Meta:
        """Classe de metadados"""

        model = ActionPlan
        fields = {
            "data_registro": ["exact", "gt", "lt", "gte", "lte"],
        }


class ServiceOrderFilter(django_filters.FilterSet):
    """Filtro para registros de presença"""

    created_at = django_filters.DateFilter(field_name="created_at")
    maint_order_status_id = django_filters.NumberFilter(lookup_expr="exact")
    order_number = django_filters.CharFilter(lookup_expr="exact")

    class Meta:
        """Classe de metadados"""

        model = ServiceOrder
        fields = {
            "created_at": ["exact", "gt", "lt", "gte", "lte"],
            "maint_order_status_id": ["exact"],
            "order_number": ["exact"],
        }


class ServiceRequestFilter(django_filters.FilterSet):
    """Filtro para registros de presença"""

    created_at = django_filters.DateFilter(field_name="created_at")
    maint_req_status_id = django_filters.NumberFilter(lookup_expr="exact")
    req_number = django_filters.CharFilter(lookup_expr="exact")

    class Meta:
        """Classe de metadados"""

        model = ServiceRequest
        fields = {
            "created_at": ["exact", "gt", "lt", "gte", "lte"],
            "maint_req_status_id": ["exact"],
            "req_number": ["exact"],
        }


class DetectorMetaisFilter(django_filters.FilterSet):
    """Filtro para registros de detector de metais"""

    data_registro = django_filters.DateFilter(field_name="data_registro")

    class Meta:
        """Classe de metadados"""

        model = DetectorMetais
        fields = {
            "data_registro": ["exact", "gt", "lt", "gte", "lte"],
            "detector_id": ["exact"],
        }
