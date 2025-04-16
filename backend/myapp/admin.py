"""
Administração do Sistema SFM
"""

# cSpell:words eficiencia

from django.contrib import admin

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

# Register your models here.
admin.site.site_header = "Administração do Sistema SFM"
admin.site.register(MaquinaInfo)
admin.site.register(MaquinaIHM)
admin.site.register(InfoIHM)
admin.site.register(QualidadeIHM)
admin.site.register(QualProd)
admin.site.register(Eficiencia)
admin.site.register(Performance)
admin.site.register(Repair)
admin.site.register(AbsenceLog)
admin.site.register(PresenceLog)
admin.site.register(ActionPlan)
admin.site.register(ServiceOrder)
admin.site.register(ServiceRequest)
