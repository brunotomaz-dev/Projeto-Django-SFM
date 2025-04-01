"""Módulo com os filtros do Django Rest Framework"""

# cSpell: words conclusao

import django_filters

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
        }


class MaquinaIHMFilter(django_filters.FilterSet):
    """Filtro de informações de IHM de máquina"""

    data_registro = django_filters.DateFilter(field_name="data_registro")

    class Meta:
        """Classe de metadados"""

        model = MaquinaIHM
        fields = {"data_registro": ["exact", "gt", "lt", "gte", "lte"]}


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
    """Filtro para registros de presença"""

    data_registro = django_filters.DateFilter(field_name="data_registro")
    conclusao = django_filters.CharFilter(lookup_expr="exact")

    class Meta:
        """Classe de metadados"""

        model = ActionPlan
        fields = {
            "data_registro": ["exact", "gt", "lt", "gte", "lte"],
            "conclusao": ["exact"],
        }
