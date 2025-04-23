"""Módulo de criação de modelos do Django"""

# cSpell:ignore usuario panificacao lideranca descricao contencao solucao responsavel conclusao
# cSpell: words maint reqs
from django.db import models


# Create your models here.
class MaquinaInfo(models.Model):
    """Modelo de informações de máquina"""

    recno = models.AutoField(primary_key=True)
    maquina_id = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    produto = models.CharField(max_length=256, null=True)
    ciclo_1_min = models.FloatField()
    ciclo_15_min = models.FloatField()
    contagem_total_ciclos = models.FloatField()
    contagem_total_produzido = models.FloatField()
    turno = models.CharField(max_length=3)
    data_registro = models.DateField()
    hora_registro = models.TimeField()
    tempo_parada = models.FloatField()
    tempo_rodando = models.FloatField()

    class Meta:
        """Definição do nome da tabela"""

        db_table = "maquina_info"

    def __str__(self):
        return (
            f"{self.maquina_id} - {self.status} - {self.data_registro} - "
            f"{self.hora_registro} - {self.produto}"
        )


class MaquinaCadastro(models.Model):
    """Modelo de cadastro de máquina"""

    recno = models.AutoField(primary_key=True)
    maquina_id = models.CharField(max_length=50)
    fabrica = models.CharField(max_length=50)
    linha = models.SmallIntegerField()
    data_registro = models.DateField()
    hora_registro = models.TimeField()
    usuario_id = models.CharField(max_length=9)

    class Meta:
        """Definição do nome da tabela"""

        db_table = "maquina_cadastro"

    def __str__(self):
        return f"{self.maquina_id} - {self.linha} - {self.data_registro} - {self.hora_registro}"


class MaquinaIHM(models.Model):
    """Modelo de informações de IHM de máquina"""

    recno = models.AutoField(primary_key=True)
    linha = models.SmallIntegerField()
    maquina_id = models.CharField(max_length=50)
    motivo = models.CharField(max_length=50)
    equipamento = models.CharField(max_length=50)
    problema = models.CharField(max_length=256)
    causa = models.CharField(max_length=256)
    os_numero = models.CharField(max_length=9)
    operador_id = models.CharField(max_length=9)
    data_registro = models.DateField()
    hora_registro = models.TimeField()
    afeta_eff = models.SmallIntegerField(default=0)  # NOTE Ajuste para o campo afeta_eff

    class Meta:
        """Definição do nome da tabela"""

        db_table = "maquina_ihm"

    def __str__(self):
        return f"{self.linha} - {self.motivo} - {self.data_registro} - {self.hora_registro}"


class InfoIHM(models.Model):
    """Modelo de informações de IHM de máquina"""

    recno = models.AutoField(primary_key=True)
    fabrica = models.SmallIntegerField()
    linha = models.SmallIntegerField()
    maquina_id = models.CharField(max_length=50)
    turno = models.CharField(max_length=3)
    status = models.CharField(max_length=10)
    data_registro = models.DateField()
    hora_registro = models.TimeField()
    motivo = models.CharField(max_length=50, null=True)
    equipamento = models.CharField(max_length=50, null=True)
    problema = models.CharField(max_length=256, null=True)
    causa = models.CharField(max_length=256, null=True)
    os_numero = models.CharField(max_length=9, null=True)
    operador_id = models.CharField(max_length=9, null=True)
    data_registro_ihm = models.DateField(null=True)
    hora_registro_ihm = models.TimeField(null=True)
    s_backup = models.CharField(max_length=50, null=True)
    data_hora = models.DateTimeField()
    data_hora_final = models.DateTimeField()
    tempo = models.IntegerField()
    afeta_eff = models.SmallIntegerField(default=0)  # NOTE Ajuste para o campo afeta_eff

    class Meta:
        """Definição do nome da tabela"""

        db_table = "analysis_info_ihm"
        indexes = [models.Index(fields=["data_registro"])]

    def __str__(self):
        return f"{self.linha} - {self.status} - {self.data_registro} - {self.hora_registro}"


class QualidadeIHM(models.Model):
    """Modelo de informações de qualidade de máquina"""

    recno = models.AutoField(primary_key=True)
    linha = models.SmallIntegerField()
    maquina_id = models.CharField(max_length=50)
    bdj_vazias = models.FloatField(null=True)
    bdj_retrabalho = models.FloatField(null=True)
    descarte_paes = models.FloatField(null=True)  # cSpell: disable-line
    descarte_paes_pasta = models.FloatField(null=True)  # cSpell: disable-line
    descarte_pasta = models.FloatField(null=True)
    data_registro = models.DateField()
    hora_registro = models.TimeField()

    class Meta:
        """Definição do nome da tabela"""

        db_table = "qualidade_ihm"
        indexes = [models.Index(fields=["data_registro"])]

    def __str__(self):
        return f"{self.linha} - {self.data_registro}"


class QualProd(models.Model):
    """Modelo de informações de qualidade de máquina"""

    recno = models.AutoField(primary_key=True)
    linha = models.SmallIntegerField()
    maquina_id = models.CharField(max_length=50)
    turno = models.CharField(max_length=3)
    data_registro = models.DateField()
    produto = models.CharField(max_length=128)
    total_ciclos = models.SmallIntegerField()
    total_produzido_sensor = models.SmallIntegerField()
    bdj_vazias = models.SmallIntegerField()
    bdj_retrabalho = models.SmallIntegerField()
    total_produzido = models.SmallIntegerField()
    descarte_paes = models.FloatField(null=True)  # cSpell: disable-line
    descarte_paes_pasta = models.FloatField(null=True)  # cSpell: disable-line
    descarte_pasta = models.FloatField(null=True)

    class Meta:
        """Definição do nome da tabela"""

        db_table = "analysis_production"
        indexes = [models.Index(fields=["data_registro"])]

    def __str__(self):
        return f"{self.linha} - {self.data_registro} - {self.produto} - {self.total_produzido}"


class Eficiencia(models.Model):
    """Modelo de informações de eficiência de máquina"""

    recno = models.AutoField(primary_key=True)
    fabrica = models.SmallIntegerField()
    linha = models.SmallIntegerField()
    maquina_id = models.CharField(max_length=8)
    turno = models.CharField(max_length=3)
    data_registro = models.DateField()
    tempo = models.SmallIntegerField()
    desconto = models.SmallIntegerField()
    excedente = models.SmallIntegerField()
    tempo_esperado = models.SmallIntegerField()
    total_produzido = models.SmallIntegerField()
    producao_esperada = models.SmallIntegerField()
    eficiencia = models.FloatField(null=True)  # cSpell: words eficiencia producao

    class Meta:
        """Definição do nome da tabela"""

        db_table = "analysis_eff"
        indexes = [models.Index(fields=["data_registro"])]

    def __str__(self):
        return f"{self.linha} - {self.data_registro} - {self.total_produzido} - {self.eficiencia}"


class Performance(models.Model):
    """Modelo de informações de eficiência de máquina"""

    recno = models.AutoField(primary_key=True)
    fabrica = models.SmallIntegerField()
    linha = models.SmallIntegerField()
    maquina_id = models.CharField(max_length=8)
    turno = models.CharField(max_length=3)
    data_registro = models.DateField()
    tempo = models.SmallIntegerField()
    desconto = models.SmallIntegerField()
    excedente = models.SmallIntegerField()
    tempo_esperado = models.SmallIntegerField()
    performance = models.FloatField(null=True)  # cSpell: words eficiencia producao

    class Meta:
        """Definição do nome da tabela"""

        db_table = "analysis_perf"
        indexes = [models.Index(fields=["data_registro"])]

    def __str__(self):
        return f"{self.linha} - {self.data_registro} - {self.performance}"


class Repair(models.Model):
    """Modelo de informações de eficiência de máquina"""

    recno = models.AutoField(primary_key=True)
    fabrica = models.SmallIntegerField()
    linha = models.SmallIntegerField()
    maquina_id = models.CharField(max_length=8)
    turno = models.CharField(max_length=3)
    data_registro = models.DateField()
    tempo = models.SmallIntegerField()
    desconto = models.SmallIntegerField()
    excedente = models.SmallIntegerField()
    tempo_esperado = models.SmallIntegerField()
    reparo = models.FloatField(null=True)

    class Meta:
        """Definição do nome da tabela"""

        db_table = "analysis_repair"
        indexes = [models.Index(fields=["data_registro"])]

    def __str__(self):
        return f"{self.linha} - {self.data_registro} - {self.reparo}"


class AbsenceLog(models.Model):
    """Tabela de Absenteísmo"""

    recno = models.AutoField(primary_key=True)
    setor = models.CharField(max_length=50)
    turno = models.CharField(max_length=3)
    nome = models.CharField(max_length=256)
    tipo = models.CharField(max_length=50)
    motivo = models.CharField(max_length=256)
    data_registro = models.DateField()
    hora_registro = models.TimeField()
    data_occ = models.DateField()
    usuario = models.CharField(max_length=50)

    class Meta:
        """Definição do nome da tabela"""

        db_table = "analysis_absent"
        indexes = [models.Index(fields=["data_registro"])]


class PresenceLog(models.Model):
    """Tabela de Presença"""

    recno = models.AutoField(primary_key=True)
    panificacao = models.SmallIntegerField(null=True)
    forno = models.SmallIntegerField(null=True)
    pasta = models.SmallIntegerField(null=True)
    recheio = models.SmallIntegerField(null=True)
    embalagem = models.SmallIntegerField(null=True)
    lideranca = models.SmallIntegerField(null=True)
    data_registro = models.DateField()
    hora_registro = models.TimeField()
    turno = models.CharField(max_length=3)
    usuario = models.CharField(max_length=50)

    class Meta:
        """Definição do nome da tabela"""

        db_table = "analysis_presence"
        indexes = [models.Index(fields=["data_registro"])]


class ActionPlan(models.Model):
    """Tabela de Plano de Ação"""

    recno = models.AutoField(primary_key=True)
    indicador = models.CharField(max_length=3)
    prioridade = models.SmallIntegerField()
    impacto = models.SmallIntegerField()
    data_registro = models.DateField()
    turno = models.CharField(max_length=3)
    descricao = models.CharField(max_length=256)
    causa_raiz = models.CharField(max_length=256)
    contencao = models.CharField(max_length=256)
    solucao = models.CharField(max_length=256)
    feedback = models.CharField(max_length=256)
    responsavel = models.CharField(max_length=50)
    data_conclusao = models.DateField(null=True)
    conclusao = models.SmallIntegerField()
    lvl = models.SmallIntegerField()

    class Meta:
        """Definição do nome da tabela"""

        db_table = "analysis_actionPlan"
        indexes = [models.Index(fields=["data_registro", "conclusao"])]


class ServiceRequest(models.Model):
    """Tabela de Solicitação de Serviço (Foreign Table do PostgreSQL)"""

    id = models.AutoField(primary_key=True)
    req_number = models.CharField(max_length=20)
    maint_req_status_id = models.IntegerField()
    solicitation = models.TextField()
    requestor = models.CharField(max_length=100)
    classification = models.IntegerField()
    created_at = models.DateTimeField()
    maint_subject_id = models.IntegerField(null=True)
    maint_subject_child_id = models.IntegerField(null=True)
    first_loc_id = models.IntegerField(null=True)
    second_loc_id = models.IntegerField(null=True)
    third_loc_id = models.IntegerField(null=True)
    asset_id = models.IntegerField(null=True)
    is_asset_stopped = models.BooleanField(default=False)
    is_security_item = models.BooleanField(default=False)

    class Meta:
        """Definição do nome da tabela"""

        managed = False  # Como é uma Foreign Table, Django não gerencia a estrutura
        db_table = "maint_reqs"

    def __str__(self):
        return f"SS {self.req_number} - {self.requestor} - {self.solicitation}"


class ServiceOrder(models.Model):
    """Tabela de Ordem de Serviço (Foreign Table do PostgreSQL)"""

    id = models.AutoField(primary_key=True)
    order_number = models.CharField(max_length=20)
    maint_order_status_id = models.IntegerField()
    description = models.TextField()
    priority = models.FloatField()
    priority_calculated = models.FloatField()
    created_at = models.DateTimeField()
    user_text = models.CharField(max_length=100)
    maint_service_type_id = models.IntegerField()
    maint_service_nature_id = models.IntegerField()
    employee_id = models.IntegerField(null=True)
    area_id = models.IntegerField()
    first_loc_id = models.IntegerField(null=True)
    second_loc_id = models.IntegerField(null=True)
    third_loc_id = models.IntegerField(null=True)
    asset_id = models.IntegerField(null=True)
    maint_req_id = models.IntegerField(null=True)
    estimated_worktime = models.FloatField(default=0)
    performed_worktime = models.FloatField(default=0)
    executed_service_historic = models.TextField(null=True)
    closed_at = models.DateTimeField(null=True)
    maint_started_at = models.DateTimeField(null=True)
    maint_finished_at = models.DateTimeField(null=True)

    class Meta:
        """Definição do nome da tabela"""

        managed = False  # Como é uma Foreign Table, Django não gerencia a estrutura
        db_table = "maint_orders"

    def __str__(self):
        return f"OS {self.order_number} - Status: {self.maint_order_status_id}"
