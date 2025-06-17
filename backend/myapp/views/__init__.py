"""This module initializes the views for the application."""

from .absenteismo import AbsenceViewSet, PresenceLogViewSet
from .action_plan import ActionPlanViewSet
from .auth import CustomTokenObtainPairView, RegisterView, change_password
from .clp_omron import PLCViewSet
from .detector_metais import DetectorMetaisViewSet
from .indicadores import EficienciaViewSet, PerformanceViewSet, RepairViewSet
from .info_ihm import InfoIHMViewSet
from .manusis import AssetsPreventiveViewSet, ServiceOrderViewSet, ServiceRequestViewSet
from .maquina_ihm import MaquinaIHMViewSet
from .maquina_info import MaqInfoHourProductionViewSet, MaquinaInfoViewSet
from .production import MaquinaInfoProductionViewSet, QualProdViewSet
from .protheus import CartCountViewSet, StockOnCFViewSet, StockStatusViewSet
from .qualidade import QualidadeIHMViewSet

__all__ = [
    "CustomTokenObtainPairView",
    "RegisterView",
    "change_password",
    "MaqInfoHourProductionViewSet",
    "MaquinaInfoViewSet",
    "MaquinaIHMViewSet",
    "InfoIHMViewSet",
    "QualidadeIHMViewSet",
    "QualProdViewSet",
    "MaquinaInfoProductionViewSet",
    "EficienciaViewSet",
    "PerformanceViewSet",
    "RepairViewSet",
    "AbsenceViewSet",
    "PresenceLogViewSet",
    "ActionPlanViewSet",
    "DetectorMetaisViewSet",
    "CartCountViewSet",
    "StockOnCFViewSet",
    "StockStatusViewSet",
    "PLCViewSet",
    "AssetsPreventiveViewSet",
    "ServiceOrderViewSet",
    "ServiceRequestViewSet",
]
