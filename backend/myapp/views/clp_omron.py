"""Módulo de views do Django Rest Framework para comunicação com CLP OMRON"""

from myapp.services import OmronPlcCommunicationService
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

# ================================================================================================ #
#                                               CLP                                                #
# ================================================================================================ #


class PLCViewSet(APIView):
    """
    API para comunicação com CLP OMRON.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """
        Lida com solicitação Get para ler um valor de um PLC OMRON.
        Este método lê um valor variável específico de um PLC usando o endereço IP fornecido.
        Requer que o endereço IP e o nome da variável (tag) sejam especificados na solicitação.
        Parâmetros:
        ----------
        Solicitação: Objeto de solicitação
        O objeto de solicitação HTTP contendo:
        - Query_params.ip_address: STR
        Endereço IP do PLC para se conectar com o PLC OMRON.
        - Data.tag: STR
        Nome da variável/tag do PLC para ler
        Retornos:
        -------
        Objeto de resposta com qualquer:
        - um objeto JSON contendo o nome da variável e seu valor
        - Um erro 400 se um parâmetro estiver ausente
        - Um erro de 500 se a leitura da variável falha
        """

        ip_address = request.query_params.get("ip_address", None)
        variable_name = request.data.get("tag", None)
        if not ip_address:
            return Response(
                {"error": "IP address parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not variable_name:
            return Response(
                {"error": "Variable name parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        plc_service = OmronPlcCommunicationService(ip_address)

        value = plc_service.read_variable(variable_name)

        if value is None:
            return Response(
                {"error": "Failed to read variable"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({f"{variable_name}": value})

    def post(self, request):
        """
        Lida com solicitação POST para escrever um valor em um PLC OMRON.
        Este método escreve um valor variável específico em um PLC usando o endereço IP fornecido.
        Requer que o endereço IP, o nome da variável (tag) e o valor, especificados na solicitação.

        Parâmetros:
        ----------
        Solicitação: Objeto de solicitação

        O objeto de solicitação HTTP contendo:
        - Query_params.ip_address: STR

        - Data.tag: STR
        - Data.value: STR
        Nome da variável/tag do PLC para escrever
        - Valor a ser escrito na variável/tag do PLC

        Retornos:
        -------
        Objeto de resposta com qualquer:
        - um objeto JSON contendo o nome da variável e seu valor
        - Um erro 400 se um parâmetro estiver ausente
        - Um erro de 500 se a escrita da variável falhar
        """
        ip_address = request.query_params.get("ip_address", None)
        variable_name = request.data.get("tag", None)
        value = request.data.get("value", None)

        if not ip_address:
            return Response(
                {"error": "IP address parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not variable_name:
            return Response(
                {"error": "Variable name parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if value is None:
            return Response(
                {"error": "Value parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        plc_service = OmronPlcCommunicationService(ip_address)

        success = plc_service.write_variable(variable_name, value)

        if not success:
            return Response(
                {"error": "Failed to write variable"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({f"{variable_name}": f"{value}", "success": True})
