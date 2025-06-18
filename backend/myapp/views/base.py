"""Views base para suporte a campos dinâmicos em Serializers"""

from rest_framework import viewsets


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
