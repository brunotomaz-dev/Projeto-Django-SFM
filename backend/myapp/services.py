"""Serviços para comunicação com sistemas externos"""

# cSpell: disable

from aphyt import omron


class OmronPlcCommunicationService:
    """Classe de serviço para comunicação com o PLC OMRON F1."""

    def __init__(self, ip_address):
        self.ip_address = ip_address

    def write_variable(self, variable_name, value):
        """Escreve um valor em uma variável do PLC."""
        try:
            with omron.NSeries(self.ip_address) as plc:
                plc.write_variable(variable_name, value)
                return True
        except Exception as e:  # pylint: disable=w0718
            print(f"Erro ao escrever: {e}")
            return False

    def read_variable(self, variable_name):
        """Lê um valor de uma variável do PLC."""
        try:
            with omron.NSeries(self.ip_address) as plc:
                value = plc.read_variable(variable_name)
                return value
        except Exception as e:  # pylint: disable=w0718
            print(f"Erro ao ler: {e}")
            return None
