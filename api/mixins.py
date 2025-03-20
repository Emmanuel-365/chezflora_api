import csv
from io import StringIO
from django.http import StreamingHttpResponse
from rest_framework.permissions import IsAdminUser
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.decorators import action


class ExportCSVViewSetMixin:
    """
    Mixin pour ajouter une action d’export CSV à un ViewSet.
    Les classes héritantes doivent définir csv_fields et csv_filename.
    """
    csv_fields = []  # À définir dans les sous-classes (ex. ['id', 'username'])
    csv_filename = "export.csv"  # Nom par défaut du fichier

    def get_csv_data(self, obj):
        """
        Méthode à surcharger pour personnaliser les données de chaque ligne.
        Par défaut, utilise csv_fields pour extraire les attributs.
        """
        return [getattr(obj, field) if hasattr(obj, field) else '' for field in self.csv_fields]

    @extend_schema(
        description="Exporte les données au format CSV (admin uniquement).",
        responses={
            200: OpenApiExample(
                'Fichier CSV',
                value='Dépend des champs définis dans csv_fields',
                media_type='text/csv'
            )
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def export_csv(self, request):
        """
        Exporte les objets du queryset dans un fichier CSV.
        """
        queryset = self.get_queryset()

        # Crée un buffer en mémoire pour le CSV
        buffer = StringIO()
        writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)

        # Écrit l’en-tête du CSV
        writer.writerow(self.csv_fields)

        # Écrit les données
        for obj in queryset:
            writer.writerow(self.get_csv_data(obj))

        # Prépare la réponse streaming
        buffer.seek(0)
        response = StreamingHttpResponse(
            buffer,
            content_type='text/csv'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.csv_filename}"'
        return response