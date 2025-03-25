# --- manage.py ---

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chezflora_api.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()


# --- projet.py ---



# --- rassemblement.py ---

import os

def collect_python_files(source_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as out:
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, source_dir)

                    # Écrire le chemin relatif en haut de chaque section
                    out.write(f"# --- {relative_path} ---\n\n")

                    # Lire et écrire le contenu du fichier
                    with open(file_path, 'r', encoding='utf-8') as f:
                        out.write(f.read() + "\n\n")

    print(f"✅ Tous les fichiers Python ont été regroupés dans : {output_file}")

if __name__ == '__main__':
    dossier_source = input("Entrez le chemin du dossier à explorer : ").strip()
    fichier_sortie = input("Entrez le nom du fichier de sortie (ex: resultat.py) : ").strip()

    collect_python_files(dossier_source, fichier_sortie)

# --- api\admin.py ---

from django.contrib import admin

# Register your models here.


# --- api\apps.py ---

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"


# --- api\exceptions.py ---

from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from django.http import JsonResponse
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Personnalise la gestion des exceptions pour retourner des réponses JSON cohérentes.
    """
    # Appelle le gestionnaire par défaut de DRF
    response = exception_handler(exc, context)

    # Si DRF n’a pas géré l’exception (ex. erreur 500 interne)
    if response is None:
        return JsonResponse({
            'error': 'Erreur interne du serveur',
            'detail': str(exc) if settings.DEBUG else 'Une erreur inattendue est survenue',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Personnalise les exceptions DRF
    if isinstance(exc, APIException):
        # Pour toutes les exceptions DRF (ex. ValidationError, PermissionDenied)
        response_data = {
            'error': exc.__class__.__name__,
            'detail': response.data.get('detail', str(exc)),
        }
        # Si c’est une ValidationError avec des champs spécifiques
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            response_data['fields'] = exc.detail
        
        response.data = response_data

    return response


# api/exceptions.py
class BannedUserException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Ce compte est banni et ne peut pas être utilisé."
    default_code = 'banned_user'

# --- api\filters.py ---

from django_filters import rest_framework as filters
from .models import (
    Utilisateur, Categorie, Produit, Promotion, Commande, Panier, Devis, Service, 
    Realisation, Abonnement, Atelier, Article, Commentaire, Parametre, Paiement
)
from django.utils import timezone

# Filtre pour Utilisateur
class UtilisateurFilter(filters.FilterSet):
    role = filters.ChoiceFilter(choices=Utilisateur._meta.get_field('role').choices)
    is_active = filters.BooleanFilter()
    is_banned = filters.BooleanFilter()

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'role', 'is_active', 'is_banned']

# Filtre pour Categorie
class CategorieFilter(filters.FilterSet):
    class Meta:
        model = Categorie
        fields = ['nom', 'is_active']

# Filtre pour Produit
class ProduitFilter(filters.FilterSet):
    categorie = filters.ModelChoiceFilter(queryset=Categorie.objects.all())
    prix_min = filters.NumberFilter(field_name='prix', lookup_expr='gte')
    prix_max = filters.NumberFilter(field_name='prix', lookup_expr='lte')
    stock_min = filters.NumberFilter(field_name='stock', lookup_expr='gte')

    class Meta:
        model = Produit
        fields = ['nom', 'categorie', 'prix_min', 'prix_max', 'stock_min', 'is_active']

# Filtre pour Promotion
class PromotionFilter(filters.FilterSet):
    date_debut = filters.DateFilter(lookup_expr='gte')
    date_fin = filters.DateFilter(lookup_expr='lte')
    status = filters.ChoiceFilter(method='filter_status', choices=[('active', 'Active'), ('expired', 'Expired')])

    class Meta:
        model = Promotion
        fields = ['nom', 'date_debut', 'date_fin', 'is_active']

    def filter_status(self, queryset, name, value):
        now = timezone.now()
        if value == 'active':
            return queryset.filter(date_debut__lte=now, date_fin__gte=now)
        elif value == 'expired':
            return queryset.filter(date_fin__lt=now)
        return queryset

# Filtre pour Commande
class CommandeFilter(filters.FilterSet):
    client = filters.ModelChoiceFilter(queryset=Utilisateur.objects.filter(role='client'))
    date_min = filters.DateFilter(field_name='date', lookup_expr='gte')
    date_max = filters.DateFilter(field_name='date', lookup_expr='lte')
    statut = filters.ChoiceFilter(choices=Commande.STATUTS)

    class Meta:
        model = Commande
        fields = ['client', 'date_min', 'date_max', 'statut', 'is_active']

# Filtre pour Panier
class PanierFilter(filters.FilterSet):
    client = filters.ModelChoiceFilter(queryset=Utilisateur.objects.filter(role='client'))

    class Meta:
        model = Panier
        fields = ['client']

# Filtre pour Devis
class DevisFilter(filters.FilterSet):
    client = filters.ModelChoiceFilter(queryset=Utilisateur.objects.filter(role='client'))
    service = filters.ModelChoiceFilter(queryset=Service.objects.all())
    statut = filters.ChoiceFilter(choices=Devis.STATUTS)

    class Meta:
        model = Devis
        fields = ['client', 'service', 'statut', 'is_active']

# Filtre pour Service
class ServiceFilter(filters.FilterSet):
    class Meta:
        model = Service
        fields = ['nom', 'is_active']

# Filtre pour Realisation
class RealisationFilter(filters.FilterSet):
    service = filters.ModelChoiceFilter(queryset=Service.objects.all())
    date_min = filters.DateFilter(field_name='date', lookup_expr='gte')

    class Meta:
        model = Realisation
        fields = ['titre', 'service', 'date_min', 'is_active']

# Filtre pour Abonnement
class AbonnementFilter(filters.FilterSet):
    client = filters.ModelChoiceFilter(queryset=Utilisateur.objects.filter(role='client'))
    type = filters.ChoiceFilter(choices=Abonnement.TYPES)
    date_debut = filters.DateFilter(lookup_expr='gte')

    class Meta:
        model = Abonnement
        fields = ['client', 'type', 'date_debut', 'is_active']

# Filtre pour Atelier
class AtelierFilter(filters.FilterSet):
    date_min = filters.DateFilter(field_name='date', lookup_expr='gte')
    places_disponibles = filters.NumberFilter(lookup_expr='gte')

    class Meta:
        model = Atelier
        fields = ['nom', 'date_min', 'places_disponibles', 'is_active']

# Filtre pour Article
class ArticleFilter(filters.FilterSet):
    admin = filters.ModelChoiceFilter(queryset=Utilisateur.objects.filter(role='admin'))
    date_publication = filters.DateFilter(lookup_expr='gte')

    class Meta:
        model = Article
        fields = ['titre', 'admin', 'date_publication', 'is_active']

# Filtre pour Commentaire
class CommentaireFilter(filters.FilterSet):
    article = filters.ModelChoiceFilter(queryset=Article.objects.all())
    client = filters.ModelChoiceFilter(queryset=Utilisateur.objects.filter(role='client'))

    class Meta:
        model = Commentaire
        fields = ['article', 'client', 'is_active']

# Filtre pour Parametre
class ParametreFilter(filters.FilterSet):
    class Meta:
        model = Parametre
        fields = ['cle']

# Filtre pour Paiement
class PaiementFilter(filters.FilterSet):
    type_transaction = filters.ChoiceFilter(choices=Paiement.TRANSACTION_TYPES)
    statut = filters.ChoiceFilter(choices=Paiement.STATUTS)
    date_min = filters.DateFilter(field_name='date', lookup_expr='gte')

    class Meta:
        model = Paiement
        fields = ['type_transaction', 'statut', 'date_min', 'is_active']

# --- api\mixins.py ---

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

# --- api\models.py ---

from datetime import timedelta
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os


def validate_image(file):
    max_size = 5 * 1024 * 1024  # 5MB
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
    validator = FileExtensionValidator(allowed_extensions)
    validator(file)
    if file.size > max_size:
        raise ValidationError("La taille de l'image ne doit pas dépasser 5MB.")


class Photo(models.Model):
    image = models.ImageField(
        upload_to='photos/%Y/%m/%d/', 
        validators=[validate_image],
        help_text="Image au format JPG, JPEG, PNG ou GIF, max 5MB"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    produit = models.ForeignKey('Produit', on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    realisation = models.ForeignKey('Realisation', on_delete=models.CASCADE, related_name='photos', null=True, blank=True)

    class Meta:
        ordering=['id']
        verbose_name = "Photo"
        verbose_name_plural = "Photos"

    def __str__(self):
        entity = None
        if hasattr(self, 'produit') and self.produit:
            entity = str(self.produit)
        elif hasattr(self, 'service') and self.service:
            entity = str(self.service)
        elif hasattr(self, 'realisation') and self.realisation:
            entity = str(self.realisation)
        return f"{entity or 'Item inconnu'} (quantité: {self.quantite})"

# Modèle Utilisateur personnalisé
class Utilisateur(AbstractUser):
    ROLES = [
        ('client', 'Client'),
        ('admin', 'Administrateur'),
    ]
    adresse = models.TextField(null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLES, default='client')
    is_active = models.BooleanField(default=False)  # Changé à True par défaut pour les admins
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    is_banned = models.BooleanField(default=False)  # Nouveau champ pour le bannissement

    class Meta:
        ordering=['id']
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.username
    

def get_otp_param(cle, default):
    try:
        return Parametre.objects.get(cle=cle).valeur
    except Parametre.DoesNotExist:
        return default

def generate_otp_code():
    length = int(get_otp_param('otp_length', '6'))
    characters = get_otp_param('otp_characters', '0123456789')
    return get_random_string(length=length, allowed_chars=characters)
# Modèle OTP
class OTP(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=20, default=generate_otp_code)  # Augmenté pour flexibilité
    date_creation = models.DateTimeField(auto_now_add=True)
    expiration = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering=['id']
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"

    def __str__(self):
        return f"OTP {self.code} pour {self.utilisateur}"

    def save(self, *args, **kwargs):
        if not self.expiration:
            validity_minutes = int(get_otp_param('otp_validity_minutes', '10'))
            self.expiration = timezone.now() + timedelta(minutes=validity_minutes)
        super().save(*args, **kwargs)

    def est_valide(self):
        return not self.is_used and timezone.now() <= self.expiration

# Modèle Catégorie
class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # Pour désactiver une catégorie sans suppression
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['id']
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.nom

# Modèle Produit
class Produit(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='produits')
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    # Plus de photos = models.JSONField(default=list, blank=True)
    # La relation avec Photo est gérée via related_name='photos'

    class Meta:
        ordering=['id']
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return f"{self.nom} ({self.categorie})"

# Modèle Promotion
class Promotion(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    reduction = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],  # Entre 0 et 1 (ex. 0.2 = 20%)
        help_text="Valeur entre 0 et 1 (ex. 0.2 pour 20%)"
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name='promotions')
    produits = models.ManyToManyField(Produit, blank=True, related_name='promotions')
    is_active = models.BooleanField(default=True)  # Activer/Désactiver la promotion
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['id']
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"

    def __str__(self):
        return f"{self.nom} ({self.reduction*100}%)"

    def est_valide(self):
        now = timezone.now()
        return self.is_active and self.date_debut <= now <= self.date_fin

# Modèle Panier
class Panier(models.Model):
    client = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='panier', limit_choices_to={'role': 'client'})
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=['id']
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"

    def __str__(self):
        return f"Panier de {self.client}"

# Modèle PanierProduit (table intermédiaire)
class PanierProduit(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='items')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='paniers')
    quantite = models.IntegerField(validators=[MinValueValidator(1)])
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['id']
        unique_together = ('panier', 'produit')  # Un produit unique par panier
        verbose_name = "Produit du panier"
        verbose_name_plural = "Produits du panier"

    def __str__(self):
        return f"{self.quantite} x {self.produit} dans {self.panier}"

# Modèle Devis
class Devis(models.Model):
    STATUTS = [
        ('brouillon', 'Brouillon'),  # Devis en cours de création par le client
        ('soumis', 'Soumis'),       # Devis envoyé à l'admin
        ('en_cours', 'En cours'),   # En cours de traitement par l'admin
        ('accepte', 'Accepté'),     # Accepté par l'admin ou le client
        ('refuse', 'Refusé'),       # Refusé par l'admin ou le client
        ('expire', 'Expiré'),       # Devis non répondu après un délai
    ]

    client = models.ForeignKey(
        'Utilisateur',
        on_delete=models.CASCADE,
        related_name='devis',
        limit_choices_to={'role': 'client'}
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE,
        related_name='devis'
    )
    description = models.TextField(
        help_text="Description détaillée de la demande du client."
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        help_text="Date de création du devis."
    )
    date_soumission = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de soumission à l'admin."
    )
    date_expiration = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date limite pour accepter/refuser le devis."
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUTS,
        default='brouillon',
        help_text="État actuel du devis."
    )
    prix_demande = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Prix demandé par le client (facultatif)."
    )
    prix_propose = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Prix proposé par l'admin."
    )
    commentaire_admin = models.TextField(
        null=True,
        blank=True,
        help_text="Commentaire ou justification de l'admin (ex. raison du refus)."
    )
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        help_text="Dernière mise à jour du devis."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indique si le devis est actif ou archivé."
    )

    class Meta:
        ordering = ['-date_creation']  # Les plus récents en premier
        verbose_name = "Devis"
        verbose_name_plural = "Devis"

    def __str__(self):
        return f"Devis #{self.id} - {self.client.username} pour {self.service.nom}"

    def calculer_expiration(self):
        """Calcule la date d'expiration (par défaut : 30 jours après soumission)."""
        if self.date_soumission:
            return self.date_soumission + timezone.timedelta(days=30)
        return None

    def verifier_expiration(self):
        """Met à jour le statut à 'expire' si la date d'expiration est dépassée."""
        if self.date_expiration and timezone.now() > self.date_expiration and self.statut not in ['accepte', 'refuse']:
            self.statut = 'expire'
            self.save()

# Modèle Service
class Service(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # Plus de photos = models.JSONField(default=list, blank=True)
    # La relation avec Photo est gérée via related_name='photos'

    class Meta:
        ordering=['id']
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.nom

# Modèle Realisation
class Realisation(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='realisations')
    titre = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateTimeField()
    admin = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='realisations', limit_choices_to={'role': 'admin'})
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # Plus de photos = models.JSONField(default=list, blank=True)
    # La relation avec Photo est gérée via related_name='photos'

    class Meta:
        ordering=['id']
        verbose_name = "Réalisation"
        verbose_name_plural = "Réalisations"

    def __str__(self):
        return f"{self.titre} ({self.service})"

# Nouvelle table intermédiaire
class AbonnementProduit(models.Model):
    abonnement = models.ForeignKey('Abonnement', on_delete=models.CASCADE, related_name='abonnement_produits')
    produit = models.ForeignKey('Produit', on_delete=models.CASCADE)
    quantite = models.IntegerField(validators=[MinValueValidator(1)], default=1)

    class Meta:
        unique_together = ('abonnement', 'produit')
        verbose_name = "Produit d'abonnement"
        verbose_name_plural = "Produits d'abonnement"

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom} dans Abonnement #{self.abonnement.id}"

class Abonnement(models.Model):
    TYPES = [('mensuel', 'Mensuel'), ('hebdomadaire', 'Hebdomadaire'), ('annuel', 'Annuel')]
    PAIEMENT_STATUTS = [
        ('non_paye', 'Non payé'),
        ('paye_complet', 'Payé en une fois'),
        ('paye_mensuel', 'Payé mensuellement'),
    ]
    client = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPES)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0.00)    
    paiement_statut = models.CharField(max_length=20, choices=PAIEMENT_STATUTS, default='non_paye')
    prochaine_facturation = models.DateTimeField(null=True, blank=True)  # Nouvelle date de facturation
    is_active = models.BooleanField(default=True)
    prochaine_livraison = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateField(auto_now=True)
    date_mise_a_jour = models.DateField(auto_now=True)


    def calculer_prix(self):
        total = sum(Decimal(str(item.produit.prix)) * item.quantite for item in self.abonnement_produits.all())
        if self.type == 'hebdomadaire':
            total *= Decimal('4')  # 4 livraisons par mois
        elif self.type == 'annuel':
            total *= Decimal('12') * Decimal('0.9')  # 12 mois avec 10% de réduction
        return total

    def calculer_prochaine_livraison(self):
        if not self.prochaine_livraison:
            return self.date_debut
        delta = {'hebdomadaire': timedelta(days=7), 'mensuel': timedelta(days=30), 'annuel': timedelta(days=30)}.get(self.type)
        return self.prochaine_livraison + delta

    def calculer_prochaine_facturation(self):
        if self.type == 'annuel':
            return None  # Pas de facturation récurrente
        delta = {'hebdomadaire': timedelta(days=30), 'mensuel': timedelta(days=30)}.get(self.type)
        return (self.prochaine_facturation or self.date_debut) + delta

    def generer_commande(self):
        if not self.is_active or (self.date_fin and timezone.now() > self.date_fin) or self.paiement_statut == 'non_paye':
            return None
        total = sum(Decimal(str(item.produit.prix)) * item.quantite for item in self.abonnement_produits.all())
        commande = Commande.objects.create(client=self.client, total=total, statut='en_attente_livraison')
        for abo_produit in self.abonnement_produits.all():
            LigneCommande.objects.create(commande=commande, produit=abo_produit.produit, quantite=abo_produit.quantite, prix_unitaire=abo_produit.produit.prix)
        self.prochaine_livraison = self.calculer_prochaine_livraison()
        self.save()
        return commande
    
    class Meta:
        ordering=['id']

# Modèle Atelier
class Atelier(models.Model):
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    duree = models.IntegerField(help_text="Durée en minutes")
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    places_disponibles = models.IntegerField()
    places_totales = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

class Participant(models.Model):
    atelier = models.ForeignKey(Atelier, on_delete=models.CASCADE, related_name='participants')
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    date_inscription = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=[('inscrit', 'Inscrit'), ('present', 'Présent'), ('annule', 'Annulé')], default='inscrit')

    class Meta:
        ordering=['id']
        unique_together = ('atelier', 'utilisateur')

    def __str__(self):
        return f"{self.utilisateur.username} - {self.atelier.nom}"

# Modèle Article
class Article(models.Model):
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    cover = models.ImageField(upload_to='article_covers', null=True, blank=True)
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_publication = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    photos = models.ManyToManyField(Photo, related_name='articles', blank=True)  # Galerie optionnelle

    class Meta:
        ordering=['id']
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return self.titre

# Modèle Commentaire
class Commentaire(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='commentaires')
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    texte = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='reponses')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering=['id']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"

    def __str__(self):
        return f"Commentaire par {self.client} sur {self.article}"

# Modèle Parametre
class Parametre(models.Model):
    cle = models.CharField(max_length=50, unique=True)
    valeur = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=['id']
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"

    def __str__(self):
        return f"{self.cle}: {self.valeur}"
 
class Adresse(models.Model):
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='adresses')
    nom = models.CharField(max_length=100)
    rue = models.CharField(max_length=200)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=20)
    pays = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} - {self.rue}, {self.ville}"
    
    class Meta:
        ordering=['id']
    

# Modèle Commande
class Commande(models.Model):
    STATUTS = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('expediee', 'Expédiée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='commandes', limit_choices_to={'role': 'client'})
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente_paiement')
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Pour archiver sans supprimer
    adresse = models.ForeignKey(Adresse, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering=['id']
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"

    def __str__(self):
        return f"Commande #{self.id} - {self.client}"


# Modèle LigneCommande
class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='lignes_commande')
    quantite = models.IntegerField(validators=[MinValueValidator(1)])
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['id']
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"

    def __str__(self):
        return f"{self.quantite} x {self.produit} (Commande #{self.commande.id})"


# Modèle Paiement
class Paiement(models.Model):
    TRANSACTION_TYPES = [
        ('commande', 'Commande'),
        ('abonnement', 'Abonnement'),
        ('atelier', 'Atelier'),
    ]
    STATUTS = [
        ('simule', 'Simulé'),
        ('effectue', 'Effectué'),
        ('echec', 'Échec'),
    ]
    commande = models.ForeignKey(Commande, on_delete=models.SET_NULL, null=True, blank=True, related_name='paiements')
    abonnement = models.ForeignKey(Abonnement, on_delete=models.SET_NULL, null=True, blank=True, related_name='paiements')
    atelier = models.ForeignKey(Atelier, on_delete=models.SET_NULL, null=True, blank=True, related_name='paiements')
    type_transaction = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    montant = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='simule')
    is_active = models.BooleanField(default=True)
    details = models.TextField(blank=True, null=True)
    methode_paiement = models.CharField(max_length=50, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)  # Pour avg_delay

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement #{self.id} - {self.type_transaction} ({self.statut})"
   

class Wishlist(models.Model):
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='wishlist', limit_choices_to={'role': 'client'})
    produits = models.ManyToManyField(Produit, related_name='wishlists', blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=['id']
        verbose_name = "Liste de souhaits"
        verbose_name_plural = "Listes de souhaits"
        unique_together = ('client',)  # Une seule wishlist par client

    def __str__(self):
        return f"Wishlist de {self.client.username}"

# --- api\serializers.py ---

from django.utils import timezone
from decimal import Decimal
from rest_framework import serializers
from .models import (
    AbonnementProduit, Utilisateur, Categorie, Produit, Promotion, Commande, LigneCommande, Photo,
    Panier, PanierProduit, Adresse, Devis, Service, Realisation, Abonnement,
    Atelier, Article, Commentaire, Parametre, Paiement, OTP, Wishlist, Participant
)
from drf_spectacular.utils import extend_schema_field
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

def compress_and_convert_image(image):
    img = Image.open(image)
    # Si l'image a un canal alpha (RGBA), convertir en RGB
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    # Optionnel : redimensionner
    img = img.resize((800, 800), Image.LANCZOS)
    output = BytesIO()
    img.save(output, format='JPEG', quality=85)
    # Conserver l'extension originale ou forcer .jpg
    output.seek(0)
    return ContentFile(output.getvalue(), name=image.name.rsplit('.', 1)[0] + '.jpg')

class PhotoSerializer(serializers.ModelSerializer):
    entity_type = serializers.CharField(write_only=True)  # "produit", "service", etc.
    entity_id = serializers.CharField(write_only=True)    # ID de l'entité

    class Meta:
        model = Photo
        fields = ['id', 'image', 'uploaded_at', 'entity_type', 'entity_id']
        read_only_fields = ['id', 'uploaded_at']

    def validate(self, data):
        entity_type = data.get('entity_type')
        entity_id = data.get('entity_id')
        entity_models = {
            'produit': Produit,
            'service': Service,
            'realisation': Realisation,
            # Ajoutez d'autres modèles ici si nécessaire
        }

        if entity_type not in entity_models:
            raise ValidationError(f"Type d'entité invalide : {entity_type}")
        
        try:
            entity_model = entity_models[entity_type]
            entity = entity_model.objects.get(id=entity_id)
        except entity_model.DoesNotExist:
            raise ValidationError(f"{entity_type.capitalize()} avec ID {entity_id} n'existe pas.")

        # Stocker l'entité validée dans les données
        data['entity'] = entity
        return data

    def create(self, validated_data):
        entity_type = validated_data.pop('entity_type')
        validated_data.pop('entity_id')  # Pas besoin après validation
        entity = validated_data.pop('entity')

        # Compression et conversion de l'image
        validated_data['image'] = compress_and_convert_image(validated_data['image'])

        # Associer à l'entité correspondante
        if entity_type == 'produit':
            photo = Photo.objects.create(produit=entity, **validated_data)
        elif entity_type == 'service':
            photo = Photo.objects.create(service=entity, **validated_data)
        elif entity_type == 'realisation':
            photo = Photo.objects.create(realisation=entity, **validated_data)
        return photo

    def to_representation(self, instance):
        request = self.context.get('request')
        representation = super().to_representation(instance)
        representation['image'] = request.build_absolute_uri(instance.image.url) if request else instance.image.url
        # Ajouter des infos sur l'entité associée
        if instance.produit:
            representation['entity_type'] = 'produit'
            representation['entity_id'] = instance.produit.id
        elif instance.service:
            representation['entity_type'] = 'service'
            representation['entity_id'] = instance.service.id
        elif instance.realisation:
            representation['entity_type'] = 'realisation'
            representation['entity_id'] = instance.realisation.id
        return representation

# Serializer pour Utilisateur
class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'username', 'email', 'adresse', 'telephone', 'role', 'is_active', 'date_creation', 'date_mise_a_jour', 'password', 'is_banned']
        read_only_fields = ['date_creation', 'date_mise_a_jour']  # Champs non modifiables via l'API

    # Validation personnalisée pour email
    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def create(self, validated_data):
        # Crée l'utilisateur avec les données validées
        user = Utilisateur(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])  # Hache le mot de passe
        user.save()
        return user
    

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['id', 'utilisateur', 'code', 'date_creation', 'expiration', 'is_used']
        read_only_fields = ['code', 'date_creation', 'expiration', 'is_used']

    def validate_utilisateur(self, value):
        if value.is_active:
            raise serializers.ValidationError("Cet utilisateur est déjà actif.")
        return value

# Serializer pour Categorie

class CategorieSerializer(serializers.ModelSerializer):
    produits_count = serializers.SerializerMethodField()

    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'description', 'is_active', 'date_creation', 'produits_count']
        read_only_fields = ['date_creation']

    @extend_schema_field(int)  # Annotation pour indiquer que c’est un entier
    def get_produits_count(self, obj):
        return obj.produits.count()

# Serializer pour Produit
class ProduitSerializer(serializers.ModelSerializer):
    prix_reduit = serializers.SerializerMethodField()
    categorie = CategorieSerializer(read_only=True)
    categorie_id = serializers.PrimaryKeyRelatedField(queryset=Categorie.objects.all(), source='categorie', write_only=True, required=False)
    promotions = serializers.PrimaryKeyRelatedField(many=True, queryset=Promotion.objects.all(), required=False)  # Rendu optionnel
    photos = PhotoSerializer(many=True, read_only=True)
    photo_ids = serializers.PrimaryKeyRelatedField(
        queryset=Photo.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'description', 'prix', 'stock', 'photos', 'categorie', 
            'categorie_id', 'promotions', 'is_active', 'date_creation', 
            'date_mise_a_jour', 'prix_reduit', 'photo_ids',
        ]
        read_only_fields = ['date_creation', 'date_mise_a_jour']

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Le stock ne peut pas être négatif.")
        return value

    def validate_prix(self, value):
        if value < Decimal('0.00'):
            raise serializers.ValidationError("Le prix ne peut pas être négatif.")
        return value
    
    def get_prix_reduit(self, obj):
        promotions = obj.promotions.filter(
            is_active=True,
            date_debut__lte=timezone.now(),
            date_fin__gte=timezone.now()
        )
        
        # Si aucune promotion active, on retourne le prix d'origine
        if not promotions.exists():
            return float(obj.prix)

        # Appliquer chaque réduction successivement
        prix_reduit = float(obj.prix)
        for promotion in promotions:
            prix_reduit *= (1 - float(promotion.reduction))

        return round(prix_reduit, 2)  # Arrondir à 2 décimales pour plus de précision
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['categorie'] = {'id': instance.categorie.id, 'nom': instance.categorie.nom} if instance.categorie else None
        representation['promotions'] = [{'id': p.id, 'nom': p.nom} for p in instance.promotions.all()]
        return representation
    
# Serializer pour Promotion
class PromotionSerializer(serializers.ModelSerializer):
    categorie = CategorieSerializer(read_only=True)
    categorie_id = serializers.PrimaryKeyRelatedField(queryset=Categorie.objects.all(), source='categorie', write_only=True, required=False, allow_null=True)
    produits = ProduitSerializer(many=True, read_only=True)  # Liste des produits en promotion
    produit_ids = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all(), many=True, source='produits', write_only=True, required=False, allow_null=True)

    class Meta:
        model = Promotion
        fields = ['id', 'nom', 'description', 'reduction', 'date_debut', 'date_fin', 'categorie', 'categorie_id', 'produits', 'produit_ids', 'is_active', 'date_creation']
        read_only_fields = ['date_creation']

    def validate(self, data):
        if data['date_debut'] >= data['date_fin']:
            raise serializers.ValidationError("La date de début doit être antérieure à la date de fin.")
        return data
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation

# Serializer pour LigneCommande
class LigneCommandeSerializer(serializers.ModelSerializer):
    produit = ProduitSerializer(read_only=True)
    produit_id = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all(), source='produit', write_only=True)

    class Meta:
        model = LigneCommande
        fields = ['id', 'commande', 'produit', 'produit_id', 'quantite', 'prix_unitaire', 'date_creation']
        read_only_fields = ['date_creation']

# Serializer pour PanierProduit (table intermédiaire)
class PanierProduitSerializer(serializers.ModelSerializer):
    produit = ProduitSerializer(read_only=True)
    produit_id = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all(), source='produit', write_only=True)

    class Meta:
        model = PanierProduit
        fields = ['id', 'panier', 'produit', 'produit_id', 'quantite', 'date_ajout']
        read_only_fields = ['date_ajout']


# Serializer pour Panier
class PanierSerializer(serializers.ModelSerializer):
    client = UtilisateurSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.filter(role='client'), source='client', write_only=True)
    items = PanierProduitSerializer(many=True, read_only=True)  # Liste des produits dans le panier
    total = serializers.CharField(read_only=True)

    class Meta:
        model = Panier
        fields = ['id', 'client', 'client_id', 'items', 'date_creation', 'date_mise_a_jour', 'total']
        read_only_fields = ['date_creation', 'date_mise_a_jour']

# Serializer pour Service
class ServiceSerializer(serializers.ModelSerializer):
    realisations = serializers.PrimaryKeyRelatedField(many=True, read_only=True)  # Liste des réalisations associées
    photos = PhotoSerializer(many=True, read_only=True)
    photo_ids = serializers.PrimaryKeyRelatedField(
        queryset=Photo.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Service
        fields = ['id', 'nom', 'description', 'photos', 'photo_ids', 'realisations', 'is_active', 'date_creation']
        read_only_fields = ['date_creation']


class DevisSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True),
        source='service',
        write_only=True,
        required=True
    )
    client_username = serializers.CharField(source='client.username', read_only=True)

    class Meta:
        model = Devis
        fields = [
            'id',
            'client_username',
            'service',
            'service_id',
            'description',
            'date_creation',
            'date_soumission',
            'date_expiration',
            'statut',
            'prix_demande',
            'prix_propose',
            'commentaire_admin',
            'date_mise_a_jour',
            'is_active',
        ]
        read_only_fields = ['date_creation', 'date_mise_a_jour', 'date_soumission', 'client_username']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Convertir les prix en chaînes pour éviter les problèmes de précision
        if representation['prix_demande'] is not None:
            representation['prix_demande'] = str(representation['prix_demande'])
        if representation['prix_propose'] is not None:
            representation['prix_propose'] = str(representation['prix_propose'])
        return representation

    def validate(self, data):
        """Validation personnalisée."""
        if 'prix_demande' in data and data['prix_demande'] < 0:
            raise serializers.ValidationError({"prix_demande": "Le prix demandé ne peut pas être négatif."})
        if 'prix_propose' in data and data['prix_propose'] < 0:
            raise serializers.ValidationError({"prix_propose": "Le prix proposé ne peut pas être négatif."})
        return data


# Serializer pour Realisation
class RealisationSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), source='service', write_only=True)
    admin = UtilisateurSerializer(read_only=True)
    admin_id = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.filter(role='admin'), source='admin', write_only=True, allow_null=True, required=False)
    photos = PhotoSerializer(many=True, read_only=True)
    photo_ids = serializers.PrimaryKeyRelatedField(
        queryset=Photo.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Realisation
        fields = ['id', 'service', 'service_id', 'titre', 'description', 'photos', 'date', 'admin', 'admin_id', 'is_active', 'date_creation', 'photo_ids']
        read_only_fields = ['date_creation']


class AbonnementProduitSerializer(serializers.ModelSerializer):
    produit = ProduitSerializer(read_only=True)
    produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(), source='produit', write_only=True
    )

    class Meta:
        model = AbonnementProduit
        fields = ['produit', 'produit_id', 'quantite']

# Serializer pour Abonnement
class AbonnementSerializer(serializers.ModelSerializer):
    abonnement_produits = AbonnementProduitSerializer(many=True, read_only=True)
    produit_quantites = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            required=True
        ),
        write_only=True
    )
    prix = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    paiement_statut = serializers.ReadOnlyField(allow_null=True, required=False)
    client = UtilisateurSerializer(read_only=True)
    class Meta:
        model = Abonnement
        fields = ['id', 'type', 'date_debut', 'date_fin', 'abonnement_produits', 'produit_quantites', 'client', 'prochaine_facturation',
                  'prix', 'is_active', 'date_creation', 'date_mise_a_jour', 'prochaine_livraison', 'paiement_statut']
        read_only_fields = ['prix', 'date_creation', 'date_mise_a_jour', 'prochaine_livraison']

    def validate(self, data):
        if data.get('date_fin') and data['date_debut'] >= data['date_fin']:
            raise serializers.ValidationError("La date de début doit être antérieure à la date de fin.")
        if not data.get('produit_quantites'):
            raise serializers.ValidationError("Un abonnement doit inclure au moins un produit.")
        return data
    
    def create(self, validated_data):
        produit_quantites = validated_data.pop('produit_quantites')
        validated_data['client'] = self.context['request'].user
        # Créer et sauvegarder l'abonnement initialement sans prix
        abonnement = Abonnement.objects.create(**validated_data)
        # Ajouter les produits liés
        for item in produit_quantites:
            produit_id = item.get('produit_id')
            quantite = item.get('quantite', 1)
            produit = Produit.objects.get(id=produit_id)
            AbonnementProduit.objects.create(abonnement=abonnement, produit=produit, quantite=quantite)
        # Calculer le prix et mettre à jour l'abonnement
        abonnement.prix = abonnement.calculer_prix()
        abonnement.prochaine_livraison = abonnement.date_debut
        abonnement.save()  # Sauvegarder les modifications
        return abonnement

    def update(self, instance, validated_data):
        produit_quantites = validated_data.pop('produit_quantites', None)
        instance.type = validated_data.get('type', instance.type)
        instance.date_debut = validated_data.get('date_debut', instance.date_debut)
        instance.date_fin = validated_data.get('date_fin', instance.date_fin)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()

        if produit_quantites is not None:
            instance.abonnement_produits.all().delete()
            for item in produit_quantites:
                produit_id = item.get('produit_id')
                quantite = item.get('quantite', 1)
                produit = Produit.objects.get(id=produit_id)
                AbonnementProduit.objects.create(abonnement=instance, produit=produit, quantite=quantite)
            instance.prix = instance.calculer_prix()
            instance.save()

        return instance

# Serializer pour Atelier
class ParticipantSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurSerializer()

    class Meta:
        model = Participant
        fields = ['id', 'utilisateur', 'date_inscription', 'statut']

class AtelierSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Atelier
        fields = ['id', 'nom', 'description', 'date', 'duree', 'prix', 'places_disponibles', 'is_active', 'participants', 'places_totales']
        read_only_fields = ['places_disponibles', 'participants']  # Ces champs ne sont pas modifiables directement via l’API

    def create(self, validated_data):
        # Lors de la création, places_disponibles = places_totales
        atelier = Atelier(
            nom=validated_data['nom'],
            description=validated_data['description'],
            date=validated_data['date'],
            duree=validated_data['duree'],
            prix=validated_data['prix'],
            places_totales=validated_data['places_totales'],
            places_disponibles=validated_data['places_totales'],  # Initialisation automatique
            is_active=validated_data.get('is_active', True)
        )
        atelier.save()
        return atelier

    def update(self, instance, validated_data):
        # Lors de la modification, ajuster places_disponibles si places_totales change
        places_totales = validated_data.get('places_totales', instance.places_totales)
        nombre_inscrits = instance.participants.count()

        # Vérifier que places_totales ne devient pas inférieur au nombre d’inscrits
        if places_totales < nombre_inscrits:
            raise serializers.ValidationError({
                'places_totales': f'Impossible de réduire à {places_totales} places : {nombre_inscrits} participants sont inscrits.'
            })

        # Calculer la différence pour ajuster places_disponibles
        difference = places_totales - instance.places_totales
        instance.nom = validated_data.get('nom', instance.nom)
        instance.description = validated_data.get('description', instance.description)
        instance.date = validated_data.get('date', instance.date)
        instance.duree = validated_data.get('duree', instance.duree)
        instance.prix = validated_data.get('prix', instance.prix)
        instance.places_totales = places_totales
        instance.places_disponibles += difference  # Ajuster places_disponibles
        instance.is_active = validated_data.get('is_active', instance.is_active)

        # S’assurer que places_disponibles reste positif
        if instance.places_disponibles < 0:
            instance.places_disponibles = 0

        instance.save()
        return instance

    def validate_places_totales(self, value):
        # Validation pour s’assurer que places_totales est positif
        if value < 0:
            raise serializers.ValidationError("Le nombre de places totales doit être positif.")
        return value

# Serializer pour Commentaire
class CommentaireSerializer(serializers.ModelSerializer):
    client = serializers.StringRelatedField()
    reponses = serializers.SerializerMethodField()

    class Meta:
        model = Commentaire
        fields = ['id', 'article', 'client', 'texte', 'date', 'parent', 'reponses']

    def get_reponses(self, obj):
        reponses = obj.reponses.all()
        return CommentaireSerializer(reponses, many=True).data

# Serializer pour Article
class ArticleSerializer(serializers.ModelSerializer):
    auteur = serializers.StringRelatedField()    
    # Filtrer pour ne retourner que les commentaires sans parent
    commentaires_ids = CommentaireSerializer(
        many=True, 
        read_only=True, 
        source='commentaires.filter(parent__isnull=True)'
    )
    class Meta:
        model = Article
        fields = ['id', 'titre', 'contenu', 'date_publication', 'auteur', 'commentaires_ids', 'is_active', 'date_mise_a_jour', 'cover']
        read_only_fields = ['date_publication', 'date_mise_a_jour']

# Serializer pour Parametre
class ParametreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parametre
        fields = ['id', 'cle', 'valeur', 'description', 'date_mise_a_jour']
        read_only_fields = ['date_mise_a_jour']

    def validate_cle(self, value):
        if Parametre.objects.filter(cle=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Cette clé existe déjà.")
        return value

# Serializer pour Paiement
class PaiementSerializer(serializers.ModelSerializer):
    commande_id = serializers.PrimaryKeyRelatedField(queryset=Commande.objects.all(), source='commande', write_only=True, required=False)
    abonnement = AbonnementSerializer(read_only=True)
    abonnement_id = serializers.PrimaryKeyRelatedField(queryset=Abonnement.objects.all(), source='abonnement', write_only=True, required=False)
    atelier = AtelierSerializer(read_only=True)
    atelier_id = serializers.PrimaryKeyRelatedField(queryset=Atelier.objects.all(), source='atelier', write_only=True, required=False)

    class Meta:
        model = Paiement
        fields = ['id', 'commande_id', 'abonnement', 'abonnement_id', 'atelier', 'atelier_id', 
                  'type_transaction', 'montant', 'date', 'statut', 'details', 'is_active']
        read_only_fields = ['date']

    def validate(self, data):
        # Vérifier qu'une seule relation est spécifiée
        relations = [data.get('commande'), data.get('abonnement'), data.get('atelier')]
        if sum(1 for r in relations if r is not None) != 1:
            raise serializers.ValidationError("Un paiement doit être lié à une seule entité (commande, abonnement ou atelier).")
        return data


class AdresseSerializer(serializers.ModelSerializer):
    client = UtilisateurSerializer(read_only=True)
    class Meta:
        model = Adresse
        fields = ['id', 'nom', 'rue', 'ville', 'code_postal', 'pays', 'is_default', 'client']

# Serializer pour Commande
class CommandeSerializer(serializers.ModelSerializer):
    client = UtilisateurSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.filter(role='client'), source='client', write_only=True)
    lignes = LigneCommandeSerializer(many=True, read_only=True)  # Liste des lignes de commande
    paiement = PaiementSerializer(read_only=True)
    adresse = AdresseSerializer()
    class Meta:
        model = Commande
        fields = ['id', 'client', 'client_id', 'date', 'statut', 'total', 'lignes', 'is_active', 'date_mise_a_jour', 'paiement', 'adresse']
        read_only_fields = ['date', 'date_mise_a_jour']

class WishlistSerializer(serializers.ModelSerializer):
    produits = ProduitSerializer(many=True, read_only=True)
    produit_ids = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        many=True,
        source='produits',
        write_only=True
    )
    client = UtilisateurSerializer()

    class Meta:
        model = Wishlist
        fields = ['id', 'client', 'produits', 'produit_ids', 'date_creation', 'date_mise_a_jour']
        read_only_fields = ['client', 'date_creation', 'date_mise_a_jour']

# --- api\tasks.py ---

from decimal import Decimal
from celery import shared_task
from .models import Abonnement, Paiement, Produit, Utilisateur
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@shared_task
def generer_commandes_abonnements():
    now = timezone.now()
    abonnements = Abonnement.objects.filter(is_active=True, prochaine_livraison__lte=now)
    for abonnement in abonnements:
        commande = abonnement.generer_commande()
        if commande:
            # Envoyer une notification au client
            send_mail(
                'Nouvelle livraison planifiée - ChezFlora',
                f'Votre commande #{commande.id} est prête pour livraison.',
                'ChezFlora <plazarecrute@gmail.com>',
                [abonnement.client.email],
            )

@shared_task
def facturer_abonnements():
    now = timezone.now()
    abonnements = Abonnement.objects.filter(
        is_active=True,
        paiement_statut='paye_mensuel',
        prochaine_facturation__lte=now
    )
    for abonnement in abonnements:
        montant = abonnement.calculer_prix() / Decimal('1')  # Mensuel ou hebdo
        Paiement.objects.create(
            abonnement=abonnement,
            type_transaction='abonnement',
            montant=montant,
            client=abonnement.client,
            statut='simule'
        )
        abonnement.prochaine_facturation = abonnement.calculer_prochaine_facturation()
        abonnement.save()
        send_mail(
            'Facture mensuelle - ChezFlora',
            f'Paiement de {montant} FCFA pour votre abonnement {abonnement.type}.',
            'ChezFlora <plazarecrute@gmail.com>',
            [abonnement.client.email]
        )

@shared_task
def notifier_stock_faible():
    produits = Produit.objects.filter(stock__lt=5, is_active=True)
    if produits.exists():
        admins = Utilisateur.objects.filter(role='admin')
        for admin in admins:
            for produit in produits:
                subject = 'Alerte Stock Faible - ChezFlora'
                html_message = render_to_string('stock_faible_email.html', {
                    'admin_name': admin.username,
                    'produit_nom': produit.nom,
                    'stock': produit.stock,
                })
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [admin.email], html_message=html_message)
    return f"{produits.count()} produits en stock faible notifiés"


import os
from celery import shared_task
from django.conf import settings
from datetime import datetime
import subprocess

@shared_task
def backup_database():
    """
    Effectue une sauvegarde de la base de données MySQL et la stocke dans un dossier local.
    """
    # Paramètres de la base de données depuis settings.py
    db_settings = settings.DATABASES['default']
    db_name = db_settings['NAME']
    db_user = db_settings['USER']
    db_password = db_settings['PASSWORD']
    db_host = db_settings.get('HOST', 'localhost')
    db_port = db_settings.get('PORT', '5432')

    # Dossier de sauvegarde
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    # Nom du fichier avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')

    # Commande mysqldump
    command = [
        'mysqldump',
        '-h', db_host,
        '-P', db_port,
        '-u', db_user,
        f'--password={db_password}',
        db_name
    ]

    # Exécution de la commande et sauvegarde dans un fichier
    try:
        with open(backup_file, 'w') as f:
            subprocess.run(command, stdout=f, check=True)
        return f"Sauvegarde réussie : {backup_file}"
    except subprocess.CalledProcessError as e:
        return f"Erreur lors de la sauvegarde : {str(e)}"
    

@shared_task
def backup_media_files():
    """
    Sauvegarde les fichiers médias dans un dossier compressé.
    """
    media_dir = settings.MEDIA_ROOT
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'media_backup_{timestamp}.zip')
    
    try:
        subprocess.run(['zip', '-r', backup_file, media_dir], check=True)
        return f"Sauvegarde des médias réussie : {backup_file}"
    except subprocess.CalledProcessError as e:
        return f"Erreur lors de la sauvegarde des médias : {str(e)}"

# --- api\tests.py ---

from django.test import TestCase

# Create your tests here.


# --- api\urls.py ---

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactView, PhotoViewSet, UtilisateurViewSet, CategorieViewSet, ProduitViewSet, PromotionViewSet, CommandeViewSet,
    LigneCommandeViewSet, PanierViewSet, DevisViewSet, ServiceViewSet, RealisationViewSet,
    AbonnementViewSet, AtelierViewSet, ArticleViewSet, CommentaireViewSet, ParametreViewSet,
    PaiementViewSet, AdresseViewSet, WishlistViewSet
)
import sys

router = DefaultRouter()

if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
    router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateur')
    router.register(r'categories', CategorieViewSet, basename='categorie')
    router.register(r'produits', ProduitViewSet, basename='produit')
    router.register(r'promotions', PromotionViewSet, basename='promotion')
    router.register(r'commandes', CommandeViewSet, basename='commande')
    router.register(r'lignes-commande', LigneCommandeViewSet, basename='lignecommande')
    router.register(r'paniers', PanierViewSet, basename='panier')
    router.register(r'devis', DevisViewSet, basename='devis')
    router.register(r'services', ServiceViewSet, basename='service')
    router.register(r'realisations', RealisationViewSet, basename='realisation')
    router.register(r'abonnements', AbonnementViewSet, basename='abonnement')
    router.register(r'ateliers', AtelierViewSet, basename='atelier')
    router.register(r'articles', ArticleViewSet, basename='article')
    router.register(r'commentaires', CommentaireViewSet, basename='commentaire')
    router.register(r'parametres', ParametreViewSet, basename='parametre')
    router.register(r'paiements', PaiementViewSet, basename='paiement')
    router.register(r'adresses', AdresseViewSet, basename='adresse')
    router.register(r'wishlist', WishlistViewSet, basename='wishlist')
    router.register(r'photos', PhotoViewSet, basename='photo')

urlpatterns = [
    path('', include(router.urls)),
    path('contact/', ContactView.as_view(), name='contact'),
    path('register/', UtilisateurViewSet.as_view({'post': 'register'}), name='register'),
    path('verify-otp/', UtilisateurViewSet.as_view({'post': 'verify_otp'}), name='verify-otp'),
    path('resend-otp/', UtilisateurViewSet.as_view({'post': 'resend_otp'}), name='resend-otp'),
    path('ban-user/', UtilisateurViewSet.as_view({'post': 'ban_user'}), name='ban-user'),
    path('parametres/public/', ParametreViewSet.as_view({'get': 'public'}), name='parametres-public'),
    path('change-password/', UtilisateurViewSet.as_view({'post': 'change_password'}), name='change-password'),
    path('update-profile/', UtilisateurViewSet.as_view({'patch': 'update_profile'}), name='update-profile'),
]

# --- api\views.py ---

from datetime import timedelta
import random
import string
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.pagination import PageNumberPagination
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Q, F
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

from .models import (
    Utilisateur, Categorie, Produit, Promotion, Commande, LigneCommande, Panier, PanierProduit, Adresse, Participant,
    Devis, Service, Realisation, Abonnement, Atelier, Article, Commentaire, Parametre, Paiement, OTP, Wishlist, Photo
)
from .serializers import (
    UtilisateurSerializer, CategorieSerializer, ProduitSerializer, PromotionSerializer, AdresseSerializer,
    CommandeSerializer, LigneCommandeSerializer, PanierSerializer, PanierProduitSerializer, WishlistSerializer,
    DevisSerializer, ServiceSerializer, RealisationSerializer, AbonnementSerializer, OTPSerializer, PhotoSerializer,
    AtelierSerializer, ArticleSerializer, CommentaireSerializer, ParametreSerializer, PaiementSerializer
)
from .filters import (
    UtilisateurFilter, CategorieFilter, ProduitFilter, PromotionFilter, CommandeFilter,
    PanierFilter, DevisFilter, ServiceFilter, RealisationFilter, AbonnementFilter,
    AtelierFilter, ArticleFilter, CommentaireFilter, ParametreFilter, PaiementFilter
)
from .exceptions import BannedUserException
from django.conf import settings
from django.db.models.functions import TruncDay
from django.contrib.auth.hashers import check_password, make_password

class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            photo = serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    # Optionnel : Ajouter une action pour supprimer une photo
    def destroy(self, request, *args, **kwargs):
        photo = self.get_object()
        photo.delete()
        return Response(status=204)

# Surcharge pour la connexion avec redirection OTP pour utilisateurs inactifs
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        return super().get_token(user)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        
        if user is None:
            raise serializers.ValidationError({'detail': 'Identifiants incorrects'}, code='authorization')
        if not user.is_active:
            OTP.objects.filter(utilisateur=user).delete()
            otp = OTP.objects.create(utilisateur=user)
            subject = 'Votre code OTP pour ChezFlora'
            html_message = render_to_string('otp_email.html', {'username': user.username, 'otp_code': otp.code})
            plain_message = strip_tags(html_message)
            from_email = 'ChezFlora <plazarecrute@gmail.com>'
            to_email = user.email
            send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
            raise serializers.ValidationError(
                {'detail': 'Utilisateur non actif', 'user_id': user.id},
                code='authorization'
            )
        if user.is_banned:
            raise BannedUserException()
        
        data = super().validate(attrs)
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Throttling personnalisé
class RegisterThrottle(ScopedRateThrottle):
    scope = 'register'

class VerifyOTPThrottle(ScopedRateThrottle):
    scope = 'verify_otp'

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'per_page'
    max_page_size = 100

# ViewSet pour les utilisateurs (authentification requise sauf pour inscription/OTP)
class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UtilisateurFilter
    search_fields = ['username', 'email']
    ordering_fields = ['username', 'date_creation']
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        # Actions publiques sans authentification
        if self.action in ['register', 'verify_otp', 'resend_otp', 'reset_password']:
            return [AllowAny()]
        # Actions accessibles aux utilisateurs authentifiés
        elif self.action in ['me', 'update', 'change_password']:
            return [IsAuthenticated()]
        # Actions réservées aux admins
        return [IsAdminUser()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Utilisateur.objects.none()
        if self.request.user.role == 'admin':
            return Utilisateur.objects.all()
        return Utilisateur.objects.filter(id=self.request.user.id)

    def perform_create(self, serializer):
        user = serializer.save(role='client', is_active=False, is_banned=False)
        otp = OTP.objects.create(utilisateur=user)
        subject = 'Votre code OTP pour ChezFlora'
        html_message = render_to_string('otp_email.html', {'username': user.username, 'otp_code': otp.code})
        plain_message = strip_tags(html_message)
        from_email = 'ChezFlora <plazarecrute@gmail.com>'
        to_email = user.email
        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
        return user

    @extend_schema(
        description="Crée un nouvel utilisateur ou redirige vers OTP si existant et inactif.",
        request=UtilisateurSerializer,
        responses={201: UtilisateurSerializer}
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], throttle_classes=[RegisterThrottle])
    def register(self, request):
        serializer = UtilisateurSerializer(data=request.data)
        email = request.data.get('email')
        username = request.data.get('username')
        
        existing_user = None
        if email and Utilisateur.objects.filter(email=email).exists():
            existing_user = Utilisateur.objects.get(email=email)
        elif username and Utilisateur.objects.filter(username=username).exists():
            existing_user = Utilisateur.objects.get(username=username)
        
        if existing_user:
            if not existing_user.is_active:
                OTP.objects.filter(utilisateur=existing_user).delete()
                otp = OTP.objects.create(utilisateur=existing_user)
                subject = 'Votre code OTP pour ChezFlora'
                html_message = render_to_string('otp_email.html', {'username': existing_user.username, 'otp_code': otp.code})
                plain_message = strip_tags(html_message)
                from_email = 'ChezFlora <plazarecrute@gmail.com>'
                to_email = existing_user.email
                send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
                return Response(
                    {'error': 'Utilisateur existe mais non actif', 'user_id': existing_user.id},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.errors or {'error': 'Email ou nom d’utilisateur déjà utilisé'}, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.is_valid():
            user = self.perform_create(serializer)
            return Response({'status': 'Utilisateur créé, OTP envoyé par email', 'user_id': user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Limiter les champs modifiables pour les non-admins
        if request.user.role != 'admin':
            allowed_fields = {'username', 'email'}
            for field in request.data.keys():
                if field not in allowed_fields:
                    return Response({'error': f'Vous ne pouvez pas modifier le champ {field}'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], throttle_classes=[VerifyOTPThrottle])
    def verify_otp(self, request):
        user_id = request.data.get('user_id')
        code = request.data.get('code')
        if not user_id or not code:
            return Response({'error': 'user_id et code sont requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(Utilisateur, id=user_id)
        if user.is_banned:
            raise BannedUserException()
        
        otp = get_object_or_404(OTP, utilisateur=user, code=code)
        if otp.est_valide():
            otp.is_used = True
            otp.save()
            user.is_active = True
            user.save()
            return Response({'status': 'Compte activé'}, status=status.HTTP_200_OK)
        return Response({'error': 'OTP invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], throttle_classes=[VerifyOTPThrottle])
    def resend_otp(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = Utilisateur.objects.get(email=email, is_active=False, is_banned=False)
        except Utilisateur.DoesNotExist:
            return Response({'error': 'Aucun utilisateur inactif et non banni avec cet email'}, status=status.HTTP_404_NOT_FOUND)
        
        OTP.objects.filter(utilisateur=user).delete()
        otp = OTP.objects.create(utilisateur=user)
        subject = 'Votre nouvel OTP pour ChezFlora'
        html_message = render_to_string('otp_email.html', {'username': user.username, 'otp_code': otp.code})
        plain_message = strip_tags(html_message)
        from_email = 'ChezFlora <plazarecrute@gmail.com>'
        to_email = user.email
        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
        return Response({'status': 'Nouvel OTP envoyé', 'user_id': user.id}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = Utilisateur.objects.get(email=email)
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            OTP.objects.create(utilisateur=user, code=token, expiration=timezone.now() + timedelta(hours=1))
            send_mail(
                'Réinitialisation de mot de passe - ChezFlora',
                f'Utilisez ce code pour réinitialiser votre mot de passe : {token}',
                'plazarecrute@gmail.com',
                [email]
            )
            return Response({'status': 'Code de réinitialisation envoyé'}, status=status.HTTP_200_OK)
        except Utilisateur.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def ban_user(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(Utilisateur, id=user_id)
        if user.role == 'admin':
            return Response({'error': 'Impossible de bannir un admin'}, status=status.HTTP_403_FORBIDDEN)
        
        user.is_active = False
        user.is_banned = True
        user.save()
        return Response({'status': 'Utilisateur banni'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Permet à un utilisateur authentifié de changer son mot de passe."""
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # Vérification des champs requis
        if not all([old_password, new_password, confirm_password]):
            return Response(
                {'error': 'Tous les champs (old_password, new_password, confirm_password) sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérification de l’ancien mot de passe
        if not check_password(old_password, user.password):
            return Response(
                {'error': 'L’ancien mot de passe est incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérification que le nouveau mot de passe et la confirmation correspondent
        if new_password != confirm_password:
            return Response(
                {'error': 'Le nouveau mot de passe et la confirmation ne correspondent pas'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Optionnel : Ajouter des règles de validation pour le nouveau mot de passe
        if len(new_password) < 8:
            return Response(
                {'error': 'Le nouveau mot de passe doit comporter au moins 8 caractères'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mise à jour du mot de passe
        user.password = make_password(new_password)
        user.save()

        return Response(
            {'status': 'Mot de passe modifié avec succès'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def dashboard(self, request):
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 7
            last_period = timezone.now() - timedelta(days=7)

        total_users = Utilisateur.objects.count()
        active_users = Utilisateur.objects.filter(is_active=True).count()
        banned_users = Utilisateur.objects.filter(is_banned=True).count()
        users_by_role = Utilisateur.objects.values('role').annotate(count=Count('id'))
        new_users_period = Utilisateur.objects.filter(date_creation__gte=last_period).count()

        total_commands = Commande.objects.count()
        commands_by_status = Commande.objects.values('statut').annotate(count=Count('id'))
        total_revenue = Commande.objects.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
        revenue_period = Commande.objects.filter(date__gte=last_period).aggregate(Sum('total'))['total__sum'] or Decimal('0.00')

        total_products = Produit.objects.count()
        active_products = Produit.objects.filter(is_active=True).count()
        low_stock_products = Produit.objects.filter(stock__lt=5, is_active=True).count()
        products_by_category = Produit.objects.filter(is_active=True).values('categorie__nom').annotate(count=Count('id'))

        total_ateliers = Atelier.objects.count()
        active_ateliers = Atelier.objects.filter(is_active=True).count()
        cancelled_ateliers = Atelier.objects.filter(is_active=False).count()
        total_participants = Atelier.objects.aggregate(total=Count('participants'))['total'] or 0

        total_payments = Paiement.objects.count()
        payments_by_type = Paiement.objects.values('type_transaction').annotate(count=Count('id'))
        total_payment_amount = Paiement.objects.aggregate(Sum('montant'))['montant__sum'] or Decimal('0.00')

        total_subscriptions = Abonnement.objects.count()
        active_subscriptions = Abonnement.objects.filter(is_active=True).count()
        subscription_revenue = Abonnement.objects.filter(is_active=True).aggregate(Sum('prix'))['prix__sum'] or Decimal('0.00')

        low_stock_details = Produit.objects.filter(stock__lt=5, is_active=True).values('id', 'nom', 'stock')

        dashboard_data = {
            'users': {
                'total': total_users,
                'active': active_users,
                'banned': banned_users,
                'by_role': {item['role']: item['count'] for item in users_by_role},
                f'new_last_{days}_days': new_users_period
            },
            'commands': {
                'total': total_commands,
                'by_status': {item['statut']: item['count'] for item in commands_by_status},
                'total_revenue': str(total_revenue),
                f'revenue_last_{days}_days': str(revenue_period)
            },
            'products': {
                'total': total_products,
                'active': active_products,
                'low_stock': low_stock_products,
                'by_category': {item['categorie__nom'] or 'Sans catégorie': item['count'] for item in products_by_category}
            },
            'ateliers': {
                'total': total_ateliers,
                'active': active_ateliers,
                'cancelled': cancelled_ateliers,
                'total_participants': total_participants
            },
            'payments': {
                'total': total_payments,
                'by_type': {item['type_transaction']: item['count'] for item in payments_by_type},
                'total_amount': str(total_payment_amount)
            },
            'subscriptions': {
                'total': total_subscriptions,
                'active': active_subscriptions,
                'total_revenue': str(subscription_revenue)
            },
            'low_stock_details': list(low_stock_details)
        }
        return Response(dashboard_data)

    def create(self, request, *args, **kwargs):
        """Création d’un utilisateur par un admin (sans OTP)."""
        if request.user.role != 'admin':
            return Response({'error': 'Réservé aux admins'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=True, is_banned=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Mise à jour d’un utilisateur par lui-même ou par un admin."""
        instance = self.get_object()

        # Vérifie si l'utilisateur est un admin ou modifie son propre profil
        if request.user.role != 'admin' and request.user.id != instance.id:
            return Response({'error': 'Vous ne pouvez modifier que votre propre profil'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Si l'utilisateur n'est pas admin, limiter les champs modifiables
        if request.user.role != 'admin':
            allowed_fields = {'username', 'email'}  # Champs modifiables par l'utilisateur
            for field in request.data.keys():
                if field not in allowed_fields:
                    return Response({'error': f'Vous ne pouvez pas modifier le champ {field}'}, status=status.HTTP_403_FORBIDDEN)

        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Suppression d’un utilisateur par un admin."""
        if request.user.role != 'admin':
            return Response({'error': 'Réservé aux admins'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 7
            last_period = timezone.now() - timedelta(days=7)

        registrations_by_day = (
            Utilisateur.objects
            .filter(date_creation__gte=last_period)
            .annotate(date=TruncDay('date_creation'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        logins_by_day = (
            Utilisateur.objects
            .filter(last_login__gte=last_period)
            .annotate(date=TruncDay('last_login'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        stats_data = {
            'registrations_by_day': [
                {'date': item['date'].strftime('%Y-%m-%d'), 'count': item['count']}
                for item in registrations_by_day
            ],
            'logins_by_day': [
                {'date': item['date'].strftime('%Y-%m-%d'), 'count': item['count']}
                for item in logins_by_day
            ],
        }
        return Response(stats_data)
    

# ViewSet pour les catégories (public par défaut)
class CategorieViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les catégories. Accessible publiquement en lecture seule.
    Modification réservée aux admins.
    """
    queryset = Categorie.objects.filter(is_active=True)
    serializer_class = CategorieSerializer
    permission_classes = [AllowAny]  # Public par défaut
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategorieFilter
    search_fields = ['nom']
    ordering_fields = ['nom', 'date_creation']
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Categorie.objects.none()
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return Categorie.objects.all()  # Admins voient toutes les catégories, actives ou non
        return Categorie.objects.filter()

# ViewSet pour les produits (public par défaut)
class ProduitViewSet(viewsets.ModelViewSet):
    serializer_class = ProduitSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProduitFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['prix', 'stock', 'date_creation']
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Produit.objects.none()
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return Produit.objects.all().order_by('id')  # Admins voient tous les produits, actifs ou non
        return Produit.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def perform_update(self, serializer):
        produit = serializer.save()
        if produit.stock < 5:
            admins = Utilisateur.objects.filter(role='admin')
            subject = 'Alerte Stock Faible - ChezFlora'
            for admin in admins:
                html_message = render_to_string('stock_faible_email.html', {
                    'admin_name': admin.username,
                    'produit_nom': produit.nom,
                    'stock': produit.stock,
                })
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [admin.email], html_message=html_message)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_photo(self, request, pk=None):
        produit = self.get_object()
        serializer = PhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(produit=produit)
            return Response(PhotoSerializer(photo).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        return {'request': self.request}
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            last_period = timezone.now() - timedelta(days=30)

        total_products = Produit.objects.count()
        active_products = Produit.objects.filter(is_active=True).count()
        low_stock_products = Produit.objects.filter(stock__lt=5, is_active=True).count()
        total_sales = (
            LigneCommande.objects
            .filter(commande__date__gte=last_period, commande__statut__in=['livree', 'expediee'])
            .aggregate(total=Sum(F('prix_unitaire') * F('quantite')))['total'] or Decimal('0.00')
        )
        sales_by_product = (
            LigneCommande.objects
            .filter(commande__date__gte=last_period, commande__statut__in=['livree', 'expediee'])
            .values('produit__id', 'produit__nom')
            .annotate(total_sales=Sum(F('prix_unitaire') * F('quantite')))
            .order_by('-total_sales')[:10]  # Top 10 produits
        )
        stock_by_category = (
            Produit.objects
            .values('categorie__nom')
            .annotate(total_stock=Sum('stock'))
            .order_by('categorie__nom')
        )
        low_stock_details = Produit.objects.filter(stock__lt=5, is_active=True).values('id', 'nom', 'stock')

        stats_data = {
            'total_products': total_products,
            'active_products': active_products,
            'low_stock_products': low_stock_products,
            'total_sales': str(total_sales),
            'sales_by_product': [
                {'produit_id': item['produit__id'], 'nom': item['produit__nom'], 'total_sales': str(item['total_sales'])}
                for item in sales_by_product
            ],
            'stock_by_category': [
                {'categorie_nom': item['categorie__nom'], 'total_stock': item['total_stock']}
                for item in stock_by_category
            ],
            'low_stock_details': list(low_stock_details),
        }
        return Response(stats_data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def low_stock(self, request):
        seuil_param = Parametre.objects.filter(cle='SEUIL_STOCK_FAIBLE').first()
        seuil = int(seuil_param.valeur) if seuil_param else 5  # Valeur par défaut : 5

        low_stock_products = Produit.objects.filter(stock__lt=seuil, is_active=True).values('id', 'nom', 'stock', 'categorie__nom')
        total_low_stock = low_stock_products.count()

        return Response({
            'seuil': seuil,
            'total_low_stock': total_low_stock,
            'products': list(low_stock_products),
        })
    
# ViewSet pour les promotions (admin seulement)
class PromotionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les promotions. Réservé aux administrateurs.
    """
    queryset = Promotion.objects.filter(is_active=True)
    serializer_class = PromotionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PromotionFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'date_debut', 'date_fin']
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Promotion.objects.none()
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return Promotion.objects.all()
        return Promotion.objects.filter(
            date_debut__lte=timezone.now(),
            date_fin__gte=timezone.now(),
            is_active=True
        )

    @action(detail=True, methods=['get'], permission_classes=[])
    def produits_affectes(self, request, pk=None):
        promotion = self.get_object()
        produits = promotion.produits.all()
        if promotion.categorie:
            produits = produits | Produit.objects.filter(categorie=promotion.categorie)
        serializer = ProduitSerializer(produits, many=True, context={'request': request})
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        # Sauvegarde initiale de la promotion
        instance = serializer.save()
        
        
        # Récupérer les produit_ids envoyés dans la requête
        produit_ids = self.request.data.get('produit_ids', [])
        
        # Si des produit_ids sont fournis, les utiliser en priorité
        if produit_ids:  # Vérifie si le champ est présent, même vide
            instance.produits.set(produit_ids)
        # Sinon, si une catégorie est spécifiée, appliquer les produits de la catégorie
        elif instance.categorie_id and instance.categorie_id is not None:
            instance.produits.set(Produit.objects.filter(categorie=instance.categorie_id))
        # Si ni produit_ids ni categorie, vider la liste (optionnel selon vos besoins)
        else:
            instance.produits.clear()

    def perform_update(self, serializer):
        # Sauvegarde des modifications
        instance = serializer.save()
        
        # Récupérer les produit_ids envoyés dans la requête
        produit_ids = self.request.data.get('produit_ids', [])
        
        # Si produit_ids est explicitement fourni (même vide), mettre à jour la liste
        if produit_ids :
            instance.produits.set(produit_ids)
        # Sinon, si une catégorie est spécifiée et pas de produit_ids explicite, utiliser la catégorie
        elif instance.categorie_id and instance.categorie_id is not None:
            instance.produits.set(Produit.objects.filter(categorie=instance.categorie_id))
        # Si ni produit_ids ni categorie, ne rien faire (conserver les produits existants)

# ViewSet pour les commandes (authentification requise)
class CommandeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les commandes. Nécessite une authentification.
    """
    serializer_class = CommandeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CommandeFilter
    search_fields = ['client__username']
    ordering_fields = ['date', 'total']
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Commande.objects.none()
        if self.request.user.role == 'admin':
            return Commande.objects.all()
        return Commande.objects.filter(client=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        commande = self.get_object()
        if commande.client != request.user and request.user.role != 'admin':
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        if commande.statut not in ['en_attente', 'en_cours']:
            return Response({'error': 'Commande déjà traitée ou annulée'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Restaurer le stock
            for ligne in commande.lignes.all():
                produit = ligne.produit
                produit.stock += ligne.quantite
                produit.save()
            
            # Gérer le paiement
            paiement = commande.paiements.first()
            if paiement:
                if paiement.statut == 'effectue':
                    paiement.statut = 'rembourse'
                    paiement.save()
                elif paiement.statut == 'simule':
                    paiement.delete()

            commande.statut = 'annulee'
            commande.save()

            # Notifier
            subject = 'Annulation de votre commande - ChezFlora'
            html_message = render_to_string('commande_annulation_email.html', {
                'client_name': commande.client.username,
                'commande_id': commande.id,
            })
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [commande.client.email], html_message=html_message)

        return Response({'status': 'Commande annulée'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def revenue(self, request):
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 7
            last_period = timezone.now() - timedelta(days=7)

        total_revenue = Commande.objects.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
        revenue_by_day = (
            Commande.objects
            .filter(date__gte=last_period)
            .annotate(day=TruncDay('date'))  # Changé 'date' en 'day' pour éviter le conflit
            .values('day')
            .annotate(total=Sum('total'))
            .order_by('day')
        )
        revenue_by_status = Commande.objects.values('statut').annotate(total=Sum('total'))

        return Response({
            'total_revenue': str(total_revenue),
            'revenue_by_day': [{'date': item['day'].strftime('%Y-%m-%d'), 'total': str(item['total'])} for item in revenue_by_day],
            'revenue_by_status': [{'statut': item['statut'], 'total': str(item['total'] or Decimal('0.00'))} for item in revenue_by_status],
        })

# ViewSet pour les lignes de commande (authentification requise)
class LigneCommandeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les lignes de commande. Nécessite une authentification.
    """
    queryset = LigneCommande.objects.all()
    serializer_class = LigneCommandeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return LigneCommande.objects.all()
        return LigneCommande.objects.filter(commande__client=self.request.user)

# ViewSet pour les paniers (authentification requise)
class PanierViewSet(viewsets.ModelViewSet):
    serializer_class = PanierSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_queryset(self):
        return Panier.objects.filter(client=self.request.user)

    def retrieve(self, request, pk=None):
        if pk == 'mon_panier':
            panier, _ = Panier.objects.get_or_create(client=request.user)
            serializer = self.get_serializer(panier)
            data = serializer.data
            total = Decimal('0.00')
            for item in panier.items.all():
                prix = item.produit.prix
                promotions = item.produit.promotions.filter(
                    is_active=True, date_debut__lte=timezone.now(), date_fin__gte=timezone.now()
                )
                if promotions.exists():
                    reduction = Decimal(str(max(p.reduction for p in promotions)))
                    prix *= (1 - reduction)
                total += prix * item.quantite
            data['total'] = "{:.2f}".format(total)
            return Response(data)  # Pas de pagination ici
        return super().retrieve(request, pk)  # Pagination appliquée si admin liste un panier spécifique

    @action(detail=True, methods=['post'])
    def ajouter_produit(self, request, pk=None):
        panier = self.get_object()
        produit_id = request.data.get('produit_id')
        quantite = int(request.data.get('quantite', 1))
        produit = get_object_or_404(Produit, id=produit_id, is_active=True)

        with transaction.atomic():
            if produit.stock < quantite:
                return Response({'error': 'Stock insuffisant'}, status=status.HTTP_400_BAD_REQUEST)
            
            panier_produit, created = PanierProduit.objects.get_or_create(
                panier=panier, produit=produit, defaults={'quantite': quantite}
            )
            if not created:
                nouvelle_quantite = panier_produit.quantite + quantite
                if produit.stock < nouvelle_quantite - panier_produit.quantite:  # Vérifie la différence
                    return Response({'error': 'Stock insuffisant pour cette quantité'}, status=status.HTTP_400_BAD_REQUEST)
                produit.stock -= quantite  # Réduit le stock
                produit.save()
                panier_produit.quantite = nouvelle_quantite
                panier_produit.save()
            else:
                produit.stock -= quantite  # Réduit le stock pour un nouvel ajout
                produit.save()

        serializer = PanierProduitSerializer(panier_produit)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def modifier_quantite(self, request, pk=None):
        panier = self.get_object()
        produit_id = request.data.get('produit_id')
        nouvelle_quantite = int(request.data.get('quantite'))
        produit = get_object_or_404(Produit, id=produit_id, is_active=True)
        panier_produit = get_object_or_404(PanierProduit, panier=panier, produit=produit)

        with transaction.atomic():
            if nouvelle_quantite <= 0:
                produit.stock += panier_produit.quantite  # Restaure le stock
                produit.save()
                panier_produit.delete()
                return Response({'status': 'Produit supprimé du panier'}, status=status.HTTP_204_NO_CONTENT)
            
            difference = nouvelle_quantite - panier_produit.quantite
            if difference > 0 and produit.stock < difference:
                return Response({'error': 'Stock insuffisant'}, status=status.HTTP_400_BAD_REQUEST)
            
            produit.stock -= difference  # Ajuste le stock (+ si négatif, - si positif)
            produit.save()
            panier_produit.quantite = nouvelle_quantite
            panier_produit.save()

        serializer = PanierProduitSerializer(panier_produit)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def supprimer_produit(self, request, pk=None):
        panier = self.get_object()
        produit_id = request.data.get('produit_id')
        produit = get_object_or_404(Produit, id=produit_id)
        panier_produit = get_object_or_404(PanierProduit, panier=panier, produit=produit)

        with transaction.atomic():
            produit.stock += panier_produit.quantite  # Restaure le stock
            produit.save()
            panier_produit.delete()

        return Response({'status': 'Produit supprimé du panier'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def valider_panier(self, request, pk=None):
        panier = self.get_object()
        if not panier.items.exists():
            return Response({'error': 'Panier vide'}, status=status.HTTP_400_BAD_REQUEST)

        adresse_id = request.data.get('adresse_id')
        if not adresse_id:
            return Response({'error': 'Adresse de livraison requise'}, status=status.HTTP_400_BAD_REQUEST)

        adresse = get_object_or_404(Adresse, id=adresse_id, client=request.user)

        with transaction.atomic():
            total = Decimal('0.00')
            commande = Commande.objects.create(client=request.user, total=total)
            for item in panier.items.all():
                prix = item.produit.prix
                promotions = item.produit.promotions.filter(
                    is_active=True, date_debut__lte=timezone.now(), date_fin__gte=timezone.now()
                )
                if promotions.exists():
                    reduction = Decimal(str(max(p.reduction for p in promotions)))
                    prix *= (1 - reduction)
                total += prix * item.quantite
                LigneCommande.objects.create(
                    commande=commande, produit=item.produit, quantite=item.quantite, prix_unitaire=prix
                )
            commande.total = total
            commande.adresse = adresse  # Ajout de l'adresse à la commande
            commande.statut = 'en_cours'
            commande.save()
            Paiement.objects.create(commande=commande, type_transaction='commande', montant=total)
            panier.items.all().delete()

        return Response({'status': 'Commande créée et paiement simulé', 'commande_id': commande.id}, status=status.HTTP_201_CREATED)


# ViewSet pour les devis (authentification requise)
class DevisViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des devis dans une application de production.
    """
    serializer_class = DevisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DevisFilter
    search_fields = ['description', 'service__nom', 'client__username']
    ordering_fields = ['date_creation', 'date_soumission', 'statut', 'prix_propose']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Devis.objects.none()
        if self.request.user.role == 'admin':
            return Devis.objects.all()
        return Devis.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        """Création d’un devis en brouillon."""
        devis = serializer.save(client=self.request.user)
        if devis.statut == 'soumis':
            self._soumettre_devis(devis)

    def perform_update(self, serializer):
        """Mise à jour d’un devis avec gestion des transitions."""
        devis = serializer.save()
        if 'statut' in serializer.validated_data:
            if devis.statut == 'soumis' and devis.date_soumission is None:
                self._soumettre_devis(devis)
            elif devis.statut in ['accepte', 'refuse']:
                self._notifier_client(devis)

    def _soumettre_devis(self, devis):
        """Logique pour soumettre un devis."""
        devis.date_soumission = timezone.now()
        devis.date_expiration = devis.calculer_expiration()
        devis.statut = 'soumis'
        devis.save()

        # Notification aux admins
        admins = Utilisateur.objects.filter(role='admin')
        subject = 'Nouveau devis soumis - ChezFlora'
        html_message = render_to_string('devis_nouveau_email.html', {
            'client_name': devis.client.username,
            'service': devis.service.nom,
            'description': devis.description,
            'prix_demande': devis.prix_demande or 'Non spécifié',
            'devis_id': devis.id,
        })
        plain_message = strip_tags(html_message)
        for admin in admins:
            send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [admin.email], html_message=html_message)

    def _notifier_client(self, devis):
        """Notifie le client lors d’une mise à jour importante."""
        subject = f"Votre devis #{devis.id} - Mise à jour"
        html_message = render_to_string('devis_reponse_email.html', {
            'client_name': devis.client.username,
            'service': devis.service.nom,
            'prix_propose': devis.prix_propose or 'Non spécifié',
            'statut': devis.get_statut_display(),
            'commentaire_admin': devis.commentaire_admin or 'Aucun commentaire',
        })
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [devis.client.email], html_message=html_message)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def soumettre(self, request, pk=None):
        """Action pour soumettre un devis (client)."""
        devis = self.get_object()
        if devis.client != self.request.user:
            return Response({'error': 'Vous ne pouvez soumettre que vos propres devis.'}, status=status.HTTP_403_FORBIDDEN)
        if devis.statut != 'brouillon':
            return Response({'error': 'Ce devis a déjà été soumis.'}, status=status.HTTP_400_BAD_REQUEST)

        devis.statut = 'soumis'
        self._soumettre_devis(devis)
        return Response({'status': 'Devis soumis avec succès', 'devis_id': devis.id}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def proposer_reponse(self, request, pk=None):
        """Action pour qu’un admin propose une réponse (prix, statut, commentaire)."""
        devis = self.get_object()
        prix_propose = request.data.get('prix_propose')
        statut = request.data.get('statut')
        commentaire_admin = request.data.get('commentaire_admin')

        # Validation
        if statut not in ['en_cours', 'accepte', 'refuse']:
            return Response({'error': 'Statut invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        if prix_propose is not None:
            try:
                prix_propose = Decimal(prix_propose)
                if prix_propose < 0:
                    return Response({'error': 'Le prix proposé ne peut pas être négatif.'}, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({'error': 'Prix proposé invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mise à jour
        devis.prix_propose = prix_propose if prix_propose is not None else devis.prix_propose
        devis.statut = statut
        devis.commentaire_admin = commentaire_admin or devis.commentaire_admin
        devis.verifier_expiration()  # Vérifie si le devis est expiré avant mise à jour
        devis.save()

        self._notifier_client(devis)
        return Response({
            'status': 'Réponse enregistrée',
            'devis_id': devis.id,
            'prix_propose': str(devis.prix_propose) if devis.prix_propose else None,
            'statut': devis.statut,
            'commentaire_admin': devis.commentaire_admin,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def accepter(self, request, pk=None):
        """Action pour qu’un client accepte un devis."""
        devis = self.get_object()
        if devis.client != self.request.user:
            return Response({'error': 'Vous ne pouvez accepter que vos propres devis.'}, status=status.HTTP_403_FORBIDDEN)
        if devis.statut not in ['en_cours', 'accepte']:
            return Response({'error': 'Ce devis ne peut pas être accepté.'}, status=status.HTTP_400_BAD_REQUEST)

        devis.statut = 'accepte'
        devis.save()
        self._notifier_client(devis)
        # TODO : Lancer une action comme créer une commande ou un paiement
        return Response({'status': 'Devis accepté', 'devis_id': devis.id}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def refuser(self, request, pk=None):
        """Action pour qu’un client refuse un devis."""
        devis = self.get_object()
        if devis.client != self.request.user:
            return Response({'error': 'Vous ne pouvez refuser que vos propres devis.'}, status=status.HTTP_403_FORBIDDEN)
        if devis.statut not in ['en_cours', 'accepte']:
            return Response({'error': 'Ce devis ne peut pas être refusé.'}, status=status.HTTP_400_BAD_REQUEST)

        devis.statut = 'refuse'
        devis.save()
        self._notifier_client(devis)
        return Response({'status': 'Devis refusé', 'devis_id': devis.id}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def statistiques(self, request):
        """Statistiques sur les devis pour les admins."""
        total_devis = Devis.objects.count()
        devis_par_statut = Devis.objects.values('statut').annotate(count=models.Count('id'))
        moyenne_prix_propose = Devis.objects.filter(prix_propose__isnull=False).aggregate(avg=models.Avg('prix_propose'))['avg'] or 0

        return Response({
            'total_devis': total_devis,
            'devis_par_statut': list(devis_par_statut),
            'moyenne_prix_propose': str(moyenne_prix_propose),
        })

# ViewSet pour les services (public par défaut)
class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les services. Accessible publiquement en lecture seule.
    Modification réservée aux admins.
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom']
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Service.objects.none()
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return Service.objects.all()
        return Service.objects.filter(is_active=True)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_photo(self, request, pk=None):
        produit = self.get_object()
        serializer = PhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(produit=produit)
            return Response(PhotoSerializer(photo).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ViewSet pour les réalisations (admin seulement)
class RealisationViewSet(viewsets.ModelViewSet):
    queryset = Realisation.objects.filter(is_active=True)
    serializer_class = RealisationSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RealisationFilter
    search_fields = ['titre', 'description']
    ordering_fields = ['date']
    pagination_class = StandardResultsSetPagination  # Ajout de la pagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(admin=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            last_period = timezone.now() - timedelta(days=30)

        total_realisations = Realisation.objects.count()
        active_realisations = Realisation.objects.filter(is_active=True).count()
        realisations_by_service = (
            Realisation.objects
            .filter(is_active=True)
            .values('service__nom')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        recent_realisations = Realisation.objects.filter(date__gte=last_period).count()

        stats_data = {
            'total_realisations': total_realisations,
            'active_realisations': active_realisations,
            'realisations_by_service': list(realisations_by_service),
            'recent_realisations': recent_realisations,
        }
        return Response(stats_data)
           
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_photo(self, request, pk=None):
        produit = self.get_object()
        serializer = PhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(produit=produit)
            return Response(PhotoSerializer(photo).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ViewSet pour les abonnements (authentification requise)
class AbonnementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les abonnements. Nécessite une authentification.
    """
    serializer_class = AbonnementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AbonnementFilter
    search_fields = ['client__username']
    ordering_fields = ['date_debut', 'prix']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Abonnement.objects.none()
        if self.request.user.role == 'admin':
            return Abonnement.objects.all()
        return Abonnement.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        with transaction.atomic():
            abonnement = serializer.save(client=self.request.user)
            # Le prix et prochaine_livraison sont déjà gérés dans create
            abonnement.prochaine_facturation = abonnement.date_debut
            # Paiement initial
            montant = abonnement.prix if abonnement.type == 'annuel' else abonnement.prix / Decimal('12' if abonnement.type == 'annuel' else '1')
            paiement = Paiement.objects.create(
                abonnement=abonnement,
                type_transaction='abonnement',
                montant=montant,
                statut='simule'
            )
            abonnement.paiement_statut = 'paye_complet' if abonnement.type == 'annuel' else 'paye_mensuel'
            abonnement.save()

            send_mail(
                'Confirmation de votre abonnement - ChezFlora',
                f'Votre abonnement {abonnement.type} a été créé. Montant: {montant} FCFA.',
                'ChezFlora <plazarecrute@gmail.com>',
                [self.request.user.email]
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def facturer(self, request, pk=None):
        abonnement = self.get_object()
        if not abonnement.is_active or not abonnement.prochaine_facturation or timezone.now() < abonnement.prochaine_facturation:
            return Response({'error': 'Pas de facturation due'}, status=status.HTTP_400_BAD_REQUEST)
        
        montant = abonnement.calculer_prix() / Decimal('12' if abonnement.type == 'annuel' else '1')
        paiement = Paiement.objects.create(
            abonnement=abonnement,
            type_transaction='abonnement',
            montant=montant,
            statut='simule'  # No 'client' here
        )
        abonnement.prochaine_facturation = abonnement.calculer_prochaine_facturation()
        abonnement.save()
        send_mail(
            'Facture de votre abonnement - ChezFlora',
            f'Paiement de {montant} FCFA pour votre abonnement {abonnement.type}.',
            'ChezFlora <plazarecrute@gmail.com>',
            [abonnement.client.email]
        )
        return Response({'status': 'Facturé', 'paiement_id': paiement.id})

    def perform_update(self, serializer):
        # Mise à jour de l'abonnement
        abonnement = serializer.save()
        # Si les produits/quantités ont changé, le prix est recalculé dans le serializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def generer_commande_manuelle(self, request, pk=None):
        abonnement = self.get_object()
        if abonnement.client != request.user and request.user.role != 'admin':
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        commande = abonnement.generer_commande()
        if commande:
            subject = 'Confirmation de votre commande - ChezFlora'
            html_message = render_to_string('commande_confirmation_email.html', {
                'client_name': commande.client.username,
                'commande_id': commande.id,
                'total': str(commande.total),  # Convertir Decimal en chaîne
                'date': commande.date.strftime('%Y-%m-%d %H:%M:%S'),
            })
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [commande.client.email], html_message=html_message)
            return Response({'status': 'Commande générée', 'commande_id': commande.id}, status=status.HTTP_201_CREATED)
        return Response({'error': 'Abonnement inactif ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        abonnement = self.get_object()
        if abonnement.client != request.user and request.user.role != 'admin':
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        if not abonnement.is_active:
            return Response({'error': 'Abonnement déjà inactif'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            abonnement.is_active = False
            abonnement.save()

            # Gérer le paiement (suppression si simulé, remboursement partiel si effectué)
            paiement = Paiement.objects.filter(abonnement=abonnement, type_transaction='abonnement').first()
            if paiement:
                if paiement.statut == 'simule':
                    paiement.delete()
                elif paiement.statut == 'effectue':
                    # Remboursement partiel basé sur le temps restant (simplifié ici)
                    paiement.statut = 'rembourse_partiel'
                    paiement.save()

            # Notifier
            subject = 'Annulation de votre abonnement - ChezFlora'
            html_message = render_to_string('abonnement_annulation_email.html', {
                'client_name': abonnement.client.username,
                'abonnement_id': abonnement.id,
            })
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [abonnement.client.email], html_message=html_message)

        return Response({'status': 'Abonnement annulé'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            last_period = timezone.now() - timedelta(days=30)

        total_abonnements = Abonnement.objects.count()
        active_abonnements = Abonnement.objects.filter(is_active=True).count()
        revenus = Abonnement.objects.filter(is_active=True).aggregate(total=Sum('prix'))['total'] or Decimal('0.00')
        abonnements_by_type = (
            Abonnement.objects
            .filter(date_debut__gte=last_period, is_active=True)
            .values('type')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        stats_data = {
            'total_abonnements': total_abonnements,
            'active_abonnements': active_abonnements,
            'revenus': str(revenus),
            'abonnements_by_type': list(abonnements_by_type),
        }
        return Response(stats_data)

# ViewSet pour les ateliers (public par défaut)
class AtelierViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les ateliers. Accessible publiquement en lecture seule.
    Modification et inscription nécessitent une authentification.
    """
    queryset = Atelier.objects.filter(is_active=True)
    serializer_class = AtelierSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AtelierFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['date', 'prix']
    csv_fields = ['id', 'nom', 'description', 'date', 'prix', 'places_disponibles']
    csv_filename = "ateliers_export.csv"
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'cancel']:
            return [IsAdminUser()]
        if self.action in ['s_inscrire', 'desinscription']:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def s_inscrire(self, request, pk=None):
        user = request.user
        atelier = self.get_object()

        if user.role != 'client':
            return Response({'error': 'Seuls les clients peuvent s’inscrire.'}, status=403)

        if atelier.places_disponibles <= 0:
            return Response({'error': 'Plus de places disponibles.'}, status=400)

        if atelier.participants.filter(utilisateur=user.id).exists():
            return Response({'error': 'Vous êtes déjà inscrit à cet atelier.'}, status=400)
        participant = Participant.objects.create(utilisateur=request.user, atelier=atelier)
        atelier.participants.add(participant)
        atelier.places_disponibles -= 1
        atelier.save()
        Paiement.objects.create(
            atelier=atelier,
            type_transaction='atelier',
            montant=atelier.prix,
        )
        return Response({'status': 'Inscription réussie et paiement simulé'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def desinscription(self, request, pk=None):
        atelier = self.get_object()
        user = request.user

        if not atelier.participants.filter(utilisateur=user.id, atelier=atelier).exists():
            return Response({'error': 'Vous n’êtes pas inscrit à cet atelier.'}, status=400)

        with transaction.atomic():
            participant=Participant.objects.get(utilisateur=user, atelier=atelier)
            participant.delete()
            atelier.places_disponibles += 1
            atelier.save()
            
            # Gérer le paiement (suppression ou remboursement)
            paiement = Paiement.objects.filter(atelier=atelier, type_transaction='atelier', montant=atelier.prix).first()
            if paiement:
                if paiement.statut == 'simule':
                    paiement.delete()
                elif paiement.statut == 'effectue':
                    paiement.statut = 'rembourse'
                    paiement.save()

            # Notifier
            subject = 'Désinscription atelier - ChezFlora'
            html_message = render_to_string('atelier_desinscription_email.html', {
                'client_name': user.username,
                'atelier_titre': atelier.nom,
            })
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [user.email], html_message=html_message)

        return Response({'status': 'Désinscription réussie', 'atelier_id': atelier.id}, status=200)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def cancel(self, request, pk=None):
        atelier = self.get_object()
        raison = request.data.get('raison')
        if not raison:
            return Response({'error': 'Raison de l’annulation requise'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            atelier.is_active = False
            atelier.save()
            
            participants = atelier.participants.all()
            for participant in participants:
                # Gérer les paiements
                paiement = Paiement.objects.filter(atelier=atelier, type_transaction='atelier', montant=atelier.prix).first()
                if paiement:
                    if paiement.statut == 'simule':
                        paiement.delete()
                    elif paiement.statut == 'effectue':
                        paiement.statut = 'rembourse'
                        paiement.save()
                
                # Notifier
                subject = 'Annulation de votre atelier - ChezFlora'
                html_message = render_to_string('atelier_cancelled_email.html', {
                    'client_name': participant.username,
                    'atelier_titre': atelier.nom,
                    'atelier_date': atelier.date.strftime('%Y-%m-%d %H:%M'),
                    'raison': raison,
                })
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [participant.email], html_message=html_message)

        return Response({'status': 'Atelier annulé, participants notifiés'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            last_period = timezone.now() - timedelta(days=30)

        total_ateliers = Atelier.objects.count()
        active_ateliers = Atelier.objects.filter(is_active=True).count()

        # Calcul des revenus totaux
        participants_count = Participant.objects.filter(
            atelier__is_active=True,
            statut='present'
        ).values('atelier__id').annotate(
            participant_count=Count('id'),
            atelier_prix=F('atelier__prix')
        ).aggregate(
            total_revenus=Sum(F('atelier_prix') * F('participant_count'))
        )['total_revenus'] or Decimal('0.00')

        inscriptions_by_atelier = (
            Participant.objects
            .filter(date_inscription__gte=last_period, statut__in=['inscrit', 'present'])
            .values('atelier__nom')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )

        stats_data = {
            'total_ateliers': total_ateliers,
            'active_ateliers': active_ateliers,
            'total_revenus': str(participants_count),
            'inscriptions_by_atelier': list(inscriptions_by_atelier),
        }
        return Response(stats_data)

    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def participants(self, request, pk=None):
        atelier = self.get_object()
        participants = atelier.participants.all()
        serializer = ParticipantSerializer(participants, many=True)
        return Response(serializer.data)

# ViewSet pour les articles (public par défaut)
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.filter(is_active=True).order_by('-date_publication')
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ArticleFilter
    search_fields = ['titre', 'contenu']
    ordering_fields = ['date_publication']
    pagination_class = StandardResultsSetPagination  # Ajout de la pagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(auteur=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        commentaires = instance.commentaires.filter(parent__isnull=True, is_active=True)
        data['commentaires'] = CommentaireSerializer(commentaires, many=True).data
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            last_period = timezone.now() - timedelta(days=30)

        total_articles = Article.objects.count()
        active_articles = Article.objects.filter(is_active=True).count()
        articles_by_author = (
            Article.objects
            .filter(is_active=True)
            .values('auteur__username')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        recent_articles = Article.objects.filter(date_publication__gte=last_period).count()
        comments_by_article = (
            Commentaire.objects
            .filter(date__gte=last_period, is_active=True)
            .values('article__titre')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]  # Top 5 articles commentés
        )

        stats_data = {
            'total_articles': total_articles,
            'active_articles': active_articles,
            'articles_by_author': list(articles_by_author),
            'recent_articles': recent_articles,
            'comments_by_article': list(comments_by_article),
        }
        return Response(stats_data)   
    
# ViewSet pour les commentaires (authentification requise)
class CommentaireViewSet(viewsets.ModelViewSet):
    serializer_class = CommentaireSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CommentaireFilter
    search_fields = ['texte']
    ordering_fields = ['date']
    pagination_class = StandardResultsSetPagination  # Ajout de la pagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'moderate']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Commentaire.objects.none()
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return Commentaire.objects.all()
        return Commentaire.objects.filter(is_active=True)

    def perform_create(self, serializer):
        article_id = self.request.data.get('article')
        parent_id = self.request.data.get('parent')
        article = get_object_or_404(Article, id=article_id)
        parent = get_object_or_404(Commentaire, id=parent_id) if parent_id else None
        serializer.save(client=self.request.user, article=article, parent=parent)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def moderate(self, request, pk=None):
        commentaire = self.get_object()
        is_active = request.data.get('is_active', None)
        if is_active is None:
            return Response({'error': 'is_active requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        commentaire.is_active = is_active
        commentaire.save()
        action = 'activé' if is_active else 'désactivé'
        return Response({'status': f'Commentaire {action}'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            last_period = timezone.now() - timedelta(days=30)

        total_comments = Commentaire.objects.count()
        active_comments = Commentaire.objects.filter(is_active=True).count()
        comments_by_day = (
            Commentaire.objects
            .filter(date__gte=last_period)
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(total=Count('id'))
            .order_by('day')
        )
        top_commenters = (
            Commentaire.objects
            .filter(is_active=True)
            .values('client__username')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )

        stats_data = {
            'total_comments': total_comments,
            'active_comments': active_comments,
            'comments_by_day': [
                {'date': item['day'].strftime('%Y-%m-%d'), 'total': item['total']}
                for item in comments_by_day
            ],
            'top_commenters': list(top_commenters),
        }
        return Response(stats_data)
        
# ViewSet pour les paramètres (public par défaut, modification admin)
class ParametreViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les paramètres. Accessible publiquement en lecture seule.
    Modification réservée aux admins.
    """
    queryset = Parametre.objects.all()
    serializer_class = ParametreSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ParametreFilter
    search_fields = ['cle', 'valeur']
    ordering_fields = ['cle']
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Parametre.objects.none()
        return Parametre.objects.all().order_by('cle')

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public(self, request):
        public_keys = ['site_name', 'site_description', 'contact_email', 'contact_phone', 'primary_color', 'secondary_color', 'background_color']
        queryset = self.queryset.filter(cle__in=public_keys)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# ViewSet pour les paiements (authentification requise)
from django.db.models import Sum, Count, Avg, Max, Min
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from rest_framework.decorators import action

from django.db.models import Sum, Count, Avg, Max, Min
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from rest_framework.decorators import action

from django.db.models import Sum, Count, Avg, Max, Min
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from rest_framework.decorators import action

class PaiementViewSet(viewsets.ModelViewSet):
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaiementFilter
    search_fields = ['type_transaction', 'methode_paiement', 'commande__id', 'abonnement__id', 'atelier__id']
    ordering_fields = ['date', 'montant']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Paiement.objects.none()
        if self.request.user.role == 'admin':
            return Paiement.objects.all()
        return Paiement.objects.filter(
            models.Q(commande__client=self.request.user) |
            models.Q(abonnement__client=self.request.user) |
            models.Q(atelier__participants__utilisateur=self.request.user)
        )

    def perform_create(self, serializer):
        paiement = serializer.save(statut='simule')
        if paiement.commande:
            paiement.commande.statut = 'en_cours'
            paiement.commande.save()
        elif paiement.abonnement:
            paiement.abonnement.is_active = True
            paiement.abonnement.save()
        elif paiement.atelier:
            paiement.atelier.participants.add(paiement.atelier.participants.first())
        subject = 'Confirmation de votre paiement - ChezFlora'
        html_message = render_to_string('paiement_confirmation.html', {
            'username': self.request.user.username,
            'montant': paiement.montant,
            'type_transaction': paiement.type_transaction,
            'transaction_id': paiement.id,
            'date': paiement.date.strftime('%Y-%m-%d %H:%M:%S'),
        })
        plain_message = strip_tags(html_message)
        from_email = 'ChezFlora <plazarecrute@gmail.com>'
        to_email = self.request.user.email
        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def simuler(self, request, pk=None):
        paiement = self.get_object()
        if paiement.statut != 'simule':
            return Response({'error': 'Paiement déjà traité'}, status=status.HTTP_400_BAD_REQUEST)
        paiement.statut = 'effectue'
        paiement.save()
        return Response({'status': 'Paiement simulé avec succès'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def rembourser(self, request, pk=None):
        paiement = self.get_object()
        if paiement.statut not in ['effectue', 'simule']:
            return Response({'error': 'Paiement déjà remboursé ou non applicable'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if paiement.commande:
                commande = paiement.commande
                commande.statut = 'annulee'
                for ligne in commande.lignes.all():
                    produit = ligne.produit
                    produit.stock += ligne.quantite
                    produit.save()
                commande.save()
            elif paiement.abonnement:
                abonnement = paiement.abonnement
                abonnement.is_active = False
                abonnement.save()
            elif paiement.atelier:
                atelier = paiement.atelier
                atelier.participants.remove(request.user)  # Simplifié, à ajuster selon contexte
                atelier.places_disponibles += 1
                atelier.save()

            paiement.statut = 'rembourse'
            paiement.save()

            email = paiement.commande.client.email if paiement.commande else \
                    paiement.abonnement.client.email if paiement.abonnement else \
                    request.user.email
            subject = 'Remboursement effectué - ChezFlora'
            html_message = render_to_string('paiement_remboursement_email.html', {
                'montant': paiement.montant,
                'type_transaction': paiement.type_transaction,
            })
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [email], html_message=html_message)

        return Response({'status': 'Paiement remboursé'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        days = request.query_params.get('days', 30)
        type_transaction = request.query_params.get('type_transaction')
        statut = request.query_params.get('statut')
        methode_paiement = request.query_params.get('methode_paiement')

        try:
            days = int(days)
            last_period = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            last_period = timezone.now() - timedelta(days=30)

        # Filtrer le queryset
        queryset = Paiement.objects.all()
        if type_transaction:
            queryset = queryset.filter(type_transaction=type_transaction)
        if statut:
            queryset = queryset.filter(statut=statut)
        if methode_paiement:
            queryset = queryset.filter(methode_paiement=methode_paiement)

        # Statistiques globales
        total_paiements = queryset.count()
        total_montant = queryset.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        avg_montant = queryset.aggregate(avg=Avg('montant'))['avg'] or Decimal('0.00')
        max_montant = queryset.aggregate(max=Max('montant'))['max'] or Decimal('0.00')
        min_montant = queryset.aggregate(min=Min('montant'))['min'] or Decimal('0.00')

        # Période spécifiée
        period_queryset = queryset.filter(date__gte=last_period)
        total_paiements_period = period_queryset.count()
        total_montant_period = period_queryset.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')

        # Par jour
        paiements_by_day = (
            period_queryset
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(count=Count('id'), total=Sum('montant'))
            .order_by('day')
        )

        # Par mois
        paiements_by_month = (
            queryset.filter(date__gte=timezone.now() - timedelta(days=365))
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(count=Count('id'), total=Sum('montant'))
            .order_by('month')
        )

        # Par année
        paiements_by_year = (
            queryset
            .annotate(year=TruncYear('date'))
            .values('year')
            .annotate(count=Count('id'), total=Sum('montant'))
            .order_by('year')
        )

        # Par type de transaction
        paiements_by_type = (
            queryset
            .values('type_transaction')
            .annotate(count=Count('id'), total=Sum('montant'))
            .order_by('-total')
        )

        # Par statut
        paiements_by_status = (
            queryset
            .values('statut')
            .annotate(count=Count('id'), total=Sum('montant'))
            .order_by('-total')
        )

        # Par méthode de paiement
        paiements_by_method = (
            queryset
            .values('methode_paiement')
            .annotate(count=Count('id'), total=Sum('montant'))
            .order_by('-total')
        )

        # Top 5 clients par type de transaction
        top_clients_commande = (
            queryset.filter(commande__isnull=False)
            .values('commande__client__username')
            .annotate(total=Sum('montant'))
            .order_by('-total')[:5]
        )
        top_clients_abonnement = (
            queryset.filter(abonnement__isnull=False)
            .values('abonnement__client__username')
            .annotate(total=Sum('montant'))
            .order_by('-total')[:5]
        )
        top_clients_atelier = (
            queryset.filter(atelier__isnull=False)
            .values('atelier__participants__utilisateur__username')
            .annotate(total=Sum('montant'))
            .order_by('-total')[:5]
        )

        # Fusionner et trier les top clients
        all_top_clients = (
            list(top_clients_commande) +
            list(top_clients_abonnement) +
            list(top_clients_atelier)
        )
        client_totals = {}
        for item in all_top_clients:
            username = (
                item.get('commande__client__username') or
                item.get('abonnement__client__username') or
                item.get('atelier__participants__utilisateur__username')
            )
            if username:
                if username in client_totals:
                    client_totals[username] += item['total']
                else:
                    client_totals[username] = item['total']
        top_clients = [
            {'client': username, 'total': str(total)}
            for username, total in sorted(client_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Taux de réussite
        success_rate = (
            queryset.filter(statut='effectue').count() / total_paiements * 100
            if total_paiements > 0 else 0
        )

        # Délai moyen
        avg_delay = (
            queryset.filter(statut='effectue')
            .aggregate(avg_delay=Avg(F('date') - F('date_creation')))['avg_delay']
        )
        avg_delay_days = avg_delay.days if avg_delay else 0

        stats_data = {
            'global': {
                'total_paiements': total_paiements,
                'total_montant': str(total_montant),
                'avg_montant': str(avg_montant),
                'max_montant': str(max_montant),
                'min_montant': str(min_montant),
                'success_rate': round(success_rate, 2),
                'avg_delay_days': avg_delay_days,
            },
            f'last_{days}_days': {
                'total_paiements': total_paiements_period,
                'total_montant': str(total_montant_period),
                'by_day': [
                    {'date': item['day'].strftime('%Y-%m-%d'), 'count': item['count'], 'total': str(item['total'])}
                    for item in paiements_by_day
                ],
            },
            'by_month_last_year': [
                {'month': item['month'].strftime('%Y-%m'), 'count': item['count'], 'total': str(item['total'])}
                for item in paiements_by_month
            ],
            'by_year': [
                {'year': item['year'].strftime('%Y'), 'count': item['count'], 'total': str(item['total'])}
                for item in paiements_by_year
            ],
            'by_type_transaction': [
                {'type': item['type_transaction'], 'count': item['count'], 'total': str(item['total'])}
                for item in paiements_by_type
            ],
            'by_status': [
                {'status': item['statut'], 'count': item['count'], 'total': str(item['total'])}
                for item in paiements_by_status
            ],
            'by_method': [
                {'method': item['methode_paiement'], 'count': item['count'], 'total': str(item['total'])}
                for item in paiements_by_method if item['methode_paiement']
            ],
            'top_clients': top_clients,
        }
        return Response(stats_data)

class AdresseViewSet(viewsets.ModelViewSet):
    serializer_class = AdresseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # Ajout des filtres
    search_fields = ['client__username', 'client__email', 'nom', 'ville']  # Recherche par utilisateur ou champs d’adresse
    ordering_fields = ['client__username', 'nom']
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Adresse.objects.none()
        if self.request.user.role == 'admin':
            return Adresse.objects.all()  # Admins voient toutes les adresses
        return Adresse.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # Ajout des filtres
    search_fields = ['client__username', 'client__email']  # Recherche par nom ou email du client
    ordering_fields = ['client__username']
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Wishlist.objects.none()
        if self.request.user.role == 'admin':
            return Wishlist.objects.all()  # Admins voient toutes les wishlists
        return Wishlist.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        # Crée ou met à jour la wishlist de l’utilisateur
        wishlist, created = Wishlist.objects.get_or_create(client=self.request.user)
        serializer.save(client=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def ajouter_produit(self, request):
        wishlist, created = Wishlist.objects.get_or_create(client=self.request.user)
        produit_id = request.data.get('produit_id')
        if not produit_id:
            return Response({'error': 'Produit ID requis.'}, status=400)
        produit = Produit.objects.filter(id=produit_id).first()
        if not produit:
            return Response({'error': 'Produit non trouvé.'}, status=404)
        if wishlist.produits.filter(id=produit_id).exists():
            return Response({'error': 'Produit déjà dans la wishlist.'}, status=400)
        wishlist.produits.add(produit)
        return Response({'status': 'Produit ajouté à la wishlist', 'produit_id': produit_id}, status=200)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def supprimer_produit(self, request):
        wishlist, created = Wishlist.objects.get_or_create(client=self.request.user)
        produit_id = request.data.get('produit_id')
        if not produit_id:
            return Response({'error': 'Produit ID requis.'}, status=400)
        produit = Produit.objects.filter(id=produit_id).first()
        if not produit:
            return Response({'error': 'Produit non trouvé.'}, status=404)
        if not wishlist.produits.filter(id=produit_id).exists():
            return Response({'error': 'Produit non dans la wishlist.'}, status=400)
        wishlist.produits.remove(produit)
        return Response({'status': 'Produit supprimé de la wishlist', 'produit_id': produit_id}, status=200)
    
    def destroy(self, request, *args, **kwargs):
        """Suppression complète d’une wishlist par un admin."""
        if request.user.role != 'admin':
            return Response({'error': 'Réservé aux admins'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ContactView(APIView):
    permission_classes = [AllowAny]  # Publique

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        message = request.data.get('message')

        if not all([name, email, message]):
            return Response({'error': 'Tous les champs sont requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Envoyer un email au support
            subject = f'Nouveau message de {name} via ChezFlora'
            body = f'Nom: {name}\nEmail: {email}\nMessage:\n{message}'
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,  # ex. 'ChezFlora <plazarecrute@gmail.com>'
                [settings.CONTACT_EMAIL],    # À définir dans settings.py (ex. 'support@chezflora.com')
                fail_silently=False,
            )
            return Response({'status': 'Message envoyé avec succès.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Erreur lors de l’envoi : {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- api\__init__.py ---



# --- api\management\commands\seed.py ---

import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from PIL import Image
from io import BytesIO
import os
from django.core.files.base import ContentFile
import pytz  # Ajout de l'importation de pytz

from api.models import (
    Utilisateur, Categorie, Produit, Promotion, Commande, LigneCommande, Panier, PanierProduit, Adresse,
    Devis, Service, Realisation, Abonnement, Atelier, Participant, Article, Commentaire, Parametre, Paiement, OTP, Wishlist, Photo
)

# Noms camerounais courants
noms = [
    "Ngono", "Mbarga", "Tchoupo", "Nguele", "Eto’o", "Abanda", "Manga", "Biya", "Fongang", "Nkoulou",
    "Essomba", "Moukoko", "Zambo", "Ondoa", "Kemajou", "Talla", "Njoya", "Djoum", "Bisseck", "Atangana",
    "Mbah", "Ndzie", "Fotso", "Ngu", "Tchami", "Ndongo", "Bekolo", "Mbodj", "Simo", "Ekambi"
]

prenoms = [
    "Jean", "Marie", "Pierre", "Paul", "Sophie", "Esther", "André", "Lucie", "Joseph", "Clément",
    "François", "Martine", "Albert", "Grace", "Samuel", "Rose", "Patrick", "Christine", "David", "Madeleine",
    "Thomas", "Anne", "Michel", "Julie", "Isaac", "Dorothée", "Philippe", "Brigitte", "Emmanuel", "Véronique"
]

# Villes camerounaises
villes = [
    "Yaoundé", "Douala", "Bamenda", "Garoua", "Maroua", "Bafoussam", "Ngaoundéré", "Buea", "Limbe", "Kumba",
    "Ebolowa", "Bertoua", "Dschang", "Foumban", "Kribi", "Sangmélima", "Nkongsamba", "Edéa", "Mbalmayo", "Tiko"
]

# Produits floraux camerounais (fleurs et arrangements)
produits_floraux = [
    ("Rose de Bafoussam", "Fleurs fraîches", Decimal("1500"), "Roses rouges cultivées à Bafoussam", 80),
    ("Lys de Douala", "Fleurs fraîches", Decimal("2000"), "Lys blancs parfumés de Douala", 60),
    ("Hibiscus rouge", "Fleurs fraîches", Decimal("1000"), "Fleurs d’hibiscus du Nord", 100),
    ("Orchidée de Buea", "Fleurs fraîches", Decimal("3000"), "Orchidées exotiques de Buea", 40),
    ("Bougainvillier", "Fleurs fraîches", Decimal("1200"), "Fleurs colorées de Kribi", 90),
    ("Bouquet Mariage Élégance", "Arrangements", Decimal("25000"), "Bouquet de roses et lys pour mariages", 20),
    ("Couronne Funéraire Paix", "Arrangements", Decimal("35000"), "Couronne de lys et orchidées", 15),
    ("Panier Floral Joie", "Arrangements", Decimal("15000"), "Panier de fleurs variées", 30),
    ("Rose éternelle", "Fleurs stabilisées", Decimal("5000"), "Rose rouge stabilisée", 50),
    ("Composition Tropicale", "Arrangements", Decimal("20000"), "Arrangement avec hibiscus et orchidées", 25),
    ("Fleur de piment", "Fleurs décoratives", Decimal("800"), "Petites fleurs rouges décoratives", 120),
    ("Bouquet Anniversaire", "Arrangements", Decimal("18000"), "Bouquet festif multicolore", 35),
    ("Pot d’orchidées", "Plantes en pot", Decimal("10000"), "Orchidée en pot pour décoration", 40),
    ("Guirlande florale", "Arrangements", Decimal("30000"), "Guirlande pour événements", 10),
    ("Ficus décoratif", "Plantes en pot", Decimal("15000"), "Plante verte pour intérieur", 30)
]

# Services floraux camerounais
services_floraux = [
    ("Décoration florale mariage", "Décoration complète avec fleurs locales", Decimal("150000")),
    ("Arrangements funéraires", "Confection de couronnes et bouquets", Decimal("80000")),
    ("Entretien de jardins", "Service d’entretien floral mensuel", Decimal("50000")),
    ("Livraison express fleurs", "Livraison rapide à domicile", Decimal("10000")),
    ("Consultation florale", "Conseils pour compositions personnalisées", Decimal("20000"))
]

# Réalisations associées aux services floraux
realisations_floraux = [
    ("Mariage à Yaoundé", "Décoration florale pour 200 invités", "2024-01-20"),
    ("Couronne funéraire Douala", "Couronne élégante pour cérémonie", "2024-02-15"),
    ("Jardin Bamiléké", "Entretien d’un jardin floral à Dschang", "2024-03-10"),
    ("Livraison Kribi", "Bouquet livré pour anniversaire", "2024-04-05"),
    ("Bouquet sur mesure", "Composition pour fête à Bamenda", "2024-05-01")
]

# Données pour les ateliers floraux
ateliers_floraux = [
    ("Confection de bouquets", "Apprendre à faire des bouquets", Decimal("12000"), 15, "2025-04-01"),
    ("Couronnes florales", "Création de couronnes décoratives", Decimal("15000"), 10, "2025-04-10"),
    ("Art floral tropical", "Techniques avec fleurs locales", Decimal("18000"), 12, "2025-04-15"),
    ("Entretien des plantes", "Conseils pour plantes en pot", Decimal("10000"), 20, "2025-04-20"),
    ("Fleurs stabilisées", "Créer des roses éternelles", Decimal("20000"), 8, "2025-04-25")
]

# Articles de blog floraux
articles_floraux = [
    ("Les fleurs du Cameroun", "Découvrez les espèces locales", "2025-01-10"),
    ("Comment entretenir vos roses", "Guide pratique pour débutants", "2025-01-15"),
    ("Fleurs pour mariages", "Idées de décoration florale", "2025-01-20"),
    ("L’hibiscus en décoration", "Utilisations et bienfaits", "2025-01-25"),
    ("Orchidées de Buea", "Secrets de culture", "2025-02-01")
]

# Commentaires pour articles
commentaires_floraux = [
    ("Très utile, merci !", "2025-01-11"),
    ("J’adore les orchidées, super article.", "2025-01-16"),
    ("Idées parfaites pour mon mariage !", "2025-01-21"),
    ("L’hibiscus est magnifique.", "2025-01-26"),
    ("Merci pour les astuces.", "2025-02-02")
]

# Promotions florales
promotions_floraux = [
    ("Promo Saint-Valentin", Decimal("0.20"), "2025-02-01", "2025-02-14"),
    ("Soldes Fête des Mères", Decimal("0.25"), "2025-05-01", "2025-05-15"),
    ("Remise Bouquets", Decimal("0.15"), "2025-06-01", "2025-06-15"),
    ("Offre Orchidées", Decimal("0.30"), "2025-07-01", "2025-07-20"),
    ("Réduction Mariage", Decimal("0.10"), "2025-08-01", "2025-08-31")
]

# Fonction pour générer une image factice
# Fonction pour générer une image factice
def generate_dummy_image(name):
    img = Image.new('RGB', (800, 800), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return ContentFile(img_byte_arr.getvalue(), f"{name}.jpg")

class Command(BaseCommand):
    help = "Seed la base de données avec des données florales camerounaises pour ChezFlora"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Début du seeding pour ChezFlora...")

        # 1. Création des utilisateurs (admins et clients)
        utilisateurs = []
        admin = Utilisateur.objects.create(
            username="admin_chezflora",
            email="admin@chezflora.cm",
            password=make_password("admin123"),
            role="admin",
            is_active=True,
            telephone="+237690123456",
            date_creation=timezone.now() - timedelta(days=365)
        )
        utilisateurs.append(admin)

        for i in range(50):  # 50 clients
            prenom = random.choice(prenoms)
            nom = random.choice(noms)
            username = f"{prenom.lower()}_{nom.lower()}{i}"
            email = f"{prenom.lower()}.{nom.lower()}@gmail.com"
            user = Utilisateur.objects.create(
                username=username,
                email=email,
                password=make_password("password123"),
                role="client",
                is_active=True,
                telephone=f"+2376{random.randint(70, 99)}{random.randint(100000, 999999)}",
                date_creation=timezone.now() - timedelta(days=random.randint(1, 300))
            )
            utilisateurs.append(user)

        self.stdout.write("Utilisateurs créés.")

        # 2. Création des adresses
        adresses = []
        for user in utilisateurs[1:]:  # Exclure l'admin
            adresse = Adresse.objects.create(
                client=user,
                nom=f"Domicile {user.username}",
                rue=f"{random.randint(1, 500)} Rue {random.choice(noms)}",
                ville=random.choice(villes),
                code_postal=f"{random.randint(1000, 9999)}",
                pays="Cameroun",
                is_default=True
            )
            adresses.append(adresse)

        self.stdout.write("Adresses créées.")

        # 3. Création des catégories
        categories = {}
        categorie_noms = set([p[1] for p in produits_floraux])
        for nom in categorie_noms:
            categorie = Categorie.objects.create(
                nom=nom,
                description=f"Catégorie pour {nom.lower()} floraux camerounais",
                is_active=True,
                date_creation=timezone.now() - timedelta(days=365)
            )
            categories[nom] = categorie

        self.stdout.write("Catégories créées.")

        # 4. Création des produits floraux
        produits = []
        for nom, cat_nom, prix, desc, stock in produits_floraux:
            produit = Produit.objects.create(
                nom=nom,
                description=desc,
                prix=prix,
                stock=stock,
                categorie=categories[cat_nom],
                is_active=True,
                date_creation=timezone.now() - timedelta(days=random.randint(1, 365))
            )
            # Ajouter une photo factice
            photo = Photo.objects.create(
                produit=produit,
                image=generate_dummy_image(f"fleur_{nom.lower().replace(' ', '_')}"),
                uploaded_at=timezone.now()
            )
            produits.append(produit)

        self.stdout.write("Produits floraux créés.")

        # 5. Création des promotions
        promotions = []
        for nom, reduction, debut, fin in promotions_floraux:
            promo = Promotion.objects.create(
                nom=nom,
                description=f"Promotion {nom} chez ChezFlora",
                reduction=reduction,
                date_debut=datetime.strptime(debut, "%Y-%m-%d").replace(tzinfo=pytz.UTC),
                date_fin=datetime.strptime(fin, "%Y-%m-%d").replace(tzinfo=pytz.UTC),
                is_active=True,
                date_creation=timezone.now() - timedelta(days=30)
            )
            # Associer aléatoirement des produits
            promo_produits = random.sample(produits, random.randint(2, 5))
            promo.produits.set(promo_produits)
            promotions.append(promo)

        self.stdout.write("Promotions créées.")

        # 6. Création des paniers et produits dans les paniers (section corrigée)
        paniers = []
        for user in utilisateurs[1:30]:  # 30 clients avec paniers
            panier = Panier.objects.create(
                client=user,
                date_creation=timezone.now() - timedelta(days=random.randint(1, 60))
            )
            produits_deja_ajoutes = set()  # Suivre les produits déjà ajoutés à ce panier
            produits_disponibles = [p for p in produits if p.stock > 0]  # Filtrer les produits avec stock > 0
            if not produits_disponibles:
                continue  # Passer au panier suivant si aucun produit n’a de stock
            for _ in range(random.randint(1, min(5, len(produits_disponibles)))):
                produit = random.choice(produits_disponibles)
                if produit.id not in produits_deja_ajoutes:  # Vérifier si le produit est déjà dans le panier
                    quantite = random.randint(1, min(3, produit.stock)) if produit.stock > 0 else 1
                    PanierProduit.objects.create(
                        panier=panier,
                        produit=produit,
                        quantite=quantite,
                        date_ajout=timezone.now() - timedelta(days=random.randint(1, 10))
                    )
                    produit.stock -= quantite
                    produit.save()
                    produits_deja_ajoutes.add(produit.id)
                    if produit.stock <= 0:
                        produits_disponibles.remove(produit)  # Retirer le produit si le stock est épuisé
                else:
                    # Si le produit existe déjà, augmenter la quantité (si le stock le permet)
                    panier_produit = PanierProduit.objects.get(panier=panier, produit=produit)
                    quantite_supplementaire = random.randint(1, min(3, produit.stock)) if produit.stock > 0 else 1
                    panier_produit.quantite += quantite_supplementaire
                    produit.stock -= quantite_supplementaire
                    produit.save()
                    panier_produit.save()
                    if produit.stock <= 0:
                        produits_disponibles.remove(produit)  # Retirer le produit si le stock est épuisé
            paniers.append(panier)

        self.stdout.write("Paniers créés.")

        # 7. Création des commandes
        commandes = []
        for user in utilisateurs[1:40]:  # 40 clients avec commandes
            adresse = random.choice(adresses)
            commande = Commande.objects.create(
                client=user,
                adresse=adresse,
                date=timezone.now() - timedelta(days=random.randint(1, 180)),
                statut=random.choice(["en_attente", "en_cours", "expediee", "livree", "annulee"]),
                total=Decimal("0.00"),
                is_active=True
            )
            total = Decimal("0.00")
            for _ in range(random.randint(1, 4)):
                produit = random.choice(produits)
                quantite = random.randint(1, min(5, produit.stock))
                prix_unitaire = produit.prix
                if produit.promotions.filter(is_active=True, date_debut__lte=timezone.now(), date_fin__gte=timezone.now()).exists():
                    promo = produit.promotions.filter(is_active=True).first()
                    prix_unitaire *= (1 - promo.reduction)
                LigneCommande.objects.create(
                    commande=commande,
                    produit=produit,
                    quantite=quantite,
                    prix_unitaire=prix_unitaire,
                    date_creation=commande.date
                )
                total += prix_unitaire * quantite
            commande.total = total
            commande.save()
            Paiement.objects.create(
                commande=commande,
                type_transaction="commande",
                montant=total,
                date=commande.date,
                statut="effectue" if commande.statut in ["expediee", "livree"] else "simule",
                is_active=True
            )
            commandes.append(commande)

        self.stdout.write("Commandes créées.")

        # 8. Création des wishlists
        wishlists = []
        for user in utilisateurs[1:25]:  # 25 clients avec wishlists
            wishlist = Wishlist.objects.create(
                client=user,
                date_creation=timezone.now() - timedelta(days=random.randint(1, 90))
            )
            wishlist_produits = random.sample(produits, random.randint(2, 6))
            wishlist.produits.set(wishlist_produits)
            wishlists.append(wishlist)

        self.stdout.write("Wishlists créées.")

        # 9. Création des services floraux
        services = []
        for nom, desc, prix in services_floraux:
            service = Service.objects.create(
                nom=nom,
                description=desc,
                is_active=True,
                date_creation=timezone.now() - timedelta(days=365)
            )
            photo = Photo.objects.create(
                service=service,
                image=generate_dummy_image(f"service_{nom.lower().replace(' ', '_')}"),
                uploaded_at=timezone.now()
            )
            services.append(service)

        self.stdout.write("Services floraux créés.")

        # 10. Création des réalisations
        realisations = []
        for nom, desc, date in realisations_floraux:
            realisation = Realisation.objects.create(
                service=random.choice(services),
                titre=nom,
                description=desc,
                date=datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=pytz.UTC),  # Correction ici
                admin=admin,
                is_active=True,
                date_creation=timezone.now() - timedelta(days=random.randint(1, 300))
            )
            photo = Photo.objects.create(
                realisation=realisation,
                image=generate_dummy_image(f"realisation_{nom.lower().replace(' ', '_')}"),
                uploaded_at=timezone.now()
            )
            realisations.append(realisation)

        self.stdout.write("Réalisations créées.")

        # 11. Création des devis
        devis = []
        for user in utilisateurs[1:20]:  # 20 clients avec devis
            service = random.choice(services)
            devis_obj = Devis.objects.create(
                client=user,
                service=service,
                description=f"Devis pour {service.nom} par {user.username}",
                date_demande=timezone.now() - timedelta(days=random.randint(1, 90)),
                statut=random.choice(["en_attente", "accepte", "refuse"]),
                prix_propose=service.prix_base * Decimal(random.uniform(0.8, 1.2)) if hasattr(service, 'prix_base') and service.prix_base else None,
                is_active=True
            )
            devis.append(devis_obj)

        self.stdout.write("Devis créés.")

        # 12. Création des abonnements floraux
        abonnements = []
        for user in utilisateurs[1:15]:  # 15 clients avec abonnements
            type_abo = random.choice(["hebdomadaire", "mensuel", "annuel"])
            produits_abo = random.sample(produits, random.randint(1, 3))
            base_price = sum(p.prix for p in produits_abo)
            if type_abo == "hebdomadaire":
                prix = base_price * Decimal("4")
            elif type_abo == "mensuel":
                prix = base_price
            else:  # annuel
                prix = base_price * Decimal("12") * Decimal("0.9")  # Réduction pour annuel
            abonnement = Abonnement.objects.create(
                client=user,
                type=type_abo,
                date_debut=timezone.now() - timedelta(days=random.randint(1, 60)),
                date_fin=timezone.now() + timedelta(days=365) if type_abo == "annuel" else None,
                prix=prix,
                is_active=True,
                date_creation=timezone.now() - timedelta(days=random.randint(1, 60)),
                prochaine_livraison=timezone.now() + timedelta(days=random.randint(1, 30))
            )
            abonnement.produits.set(produits_abo)
            Paiement.objects.create(
                abonnement=abonnement,
                type_transaction="abonnement",
                montant=prix,
                date=abonnement.date_debut,
                statut="effectue",
                is_active=True
            )
            abonnements.append(abonnement)

        self.stdout.write("Abonnements créés.")

        # 13. Création des ateliers floraux
        ateliers = []
        for nom, desc, prix, places, date in ateliers_floraux:
            atelier = Atelier.objects.create(
                nom=nom,
                description=desc,
                date=datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=pytz.UTC),
                duree=random.randint(2, 4),
                prix=prix,
                places_totales=places,
                places_disponibles=places,  # Initialement égal à places_totales
                is_active=True
            )
            # Inscription aléatoire de participants
            nombre_participants = random.randint(2, min(places, 10))  # Nombre d’inscrits
            participants = random.sample(utilisateurs[1:], nombre_participants)
            for participant in participants:
                # Créer une instance de Participant au lieu d'ajouter directement l'utilisateur
                Participant.objects.create(
                    atelier=atelier,
                    utilisateur=participant,
                    statut='inscrit'
                )
                atelier.places_disponibles -= 1  # Réduire les places disponibles
                Paiement.objects.create(
                    atelier=atelier,
                    type_transaction="atelier",
                    montant=prix,
                    date=timezone.now() - timedelta(days=random.randint(1, 30)),
                    statut="effectue",
                    is_active=True
                )
            atelier.save()  # Sauvegarder les changements
            ateliers.append(atelier)

        self.stdout.write("Ateliers créés.")

        # 14. Création des articles de blog
        articles = []
        for titre, contenu, date in articles_floraux:
            article = Article.objects.create(
                titre=titre,
                contenu=contenu,
                date_publication=datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=pytz.UTC),  # Correction ici
                auteur=admin,
                is_active=True,
                cover=generate_dummy_image(f"article_{titre.lower().replace(' ', '_')}")
            )
            articles.append(article)

        self.stdout.write("Articles créés.")

        # 15. Création des commentaires
        commentaires = []
        for texte, date in commentaires_floraux:
            commentaire = Commentaire.objects.create(
                article=random.choice(articles),
                client=random.choice(utilisateurs[1:]),
                texte=texte,
                date=datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=pytz.UTC),  # Correction ici
                is_active=True
            )
            commentaires.append(commentaire)

        self.stdout.write("Commentaires créés.")

        # 16. Création des paramètres
        parametres = [
            ("site_name", "ChezFlora", "Nom du site"),
            ("contact_email", "contact@chezflora.cm", "Email de contact"),
            ("contact_phone", "+237690123456", "Téléphone de contact"),
            ("SEUIL_STOCK_FAIBLE", "5", "Seuil pour alerte de stock faible"),
            ("primary_color", "#FF6F61", "Couleur principale du site")
        ]
        for cle, valeur, desc in parametres:
            Parametre.objects.create(cle=cle, valeur=valeur, description=desc)

        self.stdout.write("Paramètres créés.")

        self.stdout.write("Seeding terminé avec succès !")

# --- api\migrations\0001_initial.py ---

# Generated by Django 5.1.3 on 2025-03-01 12:30

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Categorie",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Catégorie",
                "verbose_name_plural": "Catégories",
            },
        ),
        migrations.CreateModel(
            name="Paiement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("id_transaction", models.IntegerField()),
                (
                    "type_transaction",
                    models.CharField(
                        choices=[
                            ("commande", "Commande"),
                            ("abonnement", "Abonnement"),
                            ("atelier", "Atelier"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "montant",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("date", models.DateTimeField(auto_now_add=True)),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("simule", "Simulé"),
                            ("effectue", "Effectué"),
                            ("echec", "Échec"),
                        ],
                        default="simule",
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("details", models.TextField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Paiement",
                "verbose_name_plural": "Paiements",
            },
        ),
        migrations.CreateModel(
            name="Parametre",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cle", models.CharField(max_length=50, unique=True)),
                ("valeur", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Paramètre",
                "verbose_name_plural": "Paramètres",
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField()),
                ("photos", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Service",
                "verbose_name_plural": "Services",
            },
        ),
        migrations.CreateModel(
            name="Utilisateur",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                ("adresse", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "telephone",
                    models.CharField(blank=True, max_length=20, null=True, unique=True),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[("client", "Client"), ("admin", "Admin")],
                        default="client",
                        max_length=10,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Utilisateur",
                "verbose_name_plural": "Utilisateurs",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Abonnement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("mensuel", "Mensuel"),
                            ("hebdomadaire", "Hebdomadaire"),
                            ("annuel", "Annuel"),
                        ],
                        max_length=20,
                    ),
                ),
                ("date_debut", models.DateTimeField()),
                ("date_fin", models.DateTimeField(blank=True, null=True)),
                (
                    "prix",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
                (
                    "client",
                    models.ForeignKey(
                        limit_choices_to={"role": "client"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="abonnements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Abonnement",
                "verbose_name_plural": "Abonnements",
            },
        ),
        migrations.CreateModel(
            name="Article",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("titre", models.CharField(max_length=100)),
                ("contenu", models.TextField()),
                ("date_publication", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
                (
                    "admin",
                    models.ForeignKey(
                        limit_choices_to={"role": "admin"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="articles",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Article",
                "verbose_name_plural": "Articles",
            },
        ),
        migrations.CreateModel(
            name="Atelier",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("titre", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("date", models.DateTimeField()),
                (
                    "places_disponibles",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(0)]
                    ),
                ),
                (
                    "prix",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                (
                    "participants",
                    models.ManyToManyField(
                        blank=True,
                        limit_choices_to={"role": "client"},
                        related_name="ateliers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Atelier",
                "verbose_name_plural": "Ateliers",
            },
        ),
        migrations.CreateModel(
            name="Commande",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateTimeField(auto_now_add=True)),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("en_cours", "En cours"),
                            ("livree", "Livrée"),
                            ("annulee", "Annulée"),
                            ("en_attente_paiement", "En attente de paiement"),
                        ],
                        default="en_attente_paiement",
                        max_length=20,
                    ),
                ),
                (
                    "total",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "client",
                    models.ForeignKey(
                        limit_choices_to={"role": "client"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="commandes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Commande",
                "verbose_name_plural": "Commandes",
            },
        ),
        migrations.CreateModel(
            name="Commentaire",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("texte", models.TextField()),
                ("date", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "article",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="commentaires",
                        to="api.article",
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        limit_choices_to={"role": "client"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="commentaires",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Commentaire",
                "verbose_name_plural": "Commentaires",
            },
        ),
        migrations.CreateModel(
            name="Panier",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
                (
                    "client",
                    models.OneToOneField(
                        limit_choices_to={"role": "client"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="panier",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Panier",
                "verbose_name_plural": "Paniers",
            },
        ),
        migrations.CreateModel(
            name="Produit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=100)),
                ("description", models.TextField()),
                (
                    "prix",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "stock",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(0)]
                    ),
                ),
                ("photos", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
                (
                    "categorie",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="produits",
                        to="api.categorie",
                    ),
                ),
            ],
            options={
                "verbose_name": "Produit",
                "verbose_name_plural": "Produits",
            },
        ),
        migrations.CreateModel(
            name="LigneCommande",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantite",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(1)]
                    ),
                ),
                (
                    "prix_unitaire",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                (
                    "commande",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lignes",
                        to="api.commande",
                    ),
                ),
                (
                    "produit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lignes_commande",
                        to="api.produit",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ligne de commande",
                "verbose_name_plural": "Lignes de commande",
            },
        ),
        migrations.CreateModel(
            name="Promotion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "reduction",
                    models.FloatField(
                        help_text="Valeur entre 0 et 1 (ex. 0.2 pour 20%)",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(1),
                        ],
                    ),
                ),
                ("date_debut", models.DateTimeField()),
                ("date_fin", models.DateTimeField()),
                ("is_active", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                (
                    "categorie",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="promotions",
                        to="api.categorie",
                    ),
                ),
                (
                    "produits",
                    models.ManyToManyField(
                        blank=True, related_name="promotions", to="api.produit"
                    ),
                ),
            ],
            options={
                "verbose_name": "Promotion",
                "verbose_name_plural": "Promotions",
            },
        ),
        migrations.CreateModel(
            name="Realisation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("titre", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("photos", models.JSONField(blank=True, default=list)),
                ("date", models.DateTimeField()),
                ("is_active", models.BooleanField(default=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                (
                    "admin",
                    models.ForeignKey(
                        limit_choices_to={"role": "admin"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="realisations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="realisations",
                        to="api.service",
                    ),
                ),
            ],
            options={
                "verbose_name": "Réalisation",
                "verbose_name_plural": "Réalisations",
            },
        ),
        migrations.CreateModel(
            name="Devis",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("description", models.TextField()),
                ("date_demande", models.DateTimeField(auto_now_add=True)),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("en_attente", "En attente"),
                            ("accepte", "Accepté"),
                            ("refuse", "Refusé"),
                        ],
                        default="en_attente",
                        max_length=20,
                    ),
                ),
                (
                    "prix_propose",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=10,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "client",
                    models.ForeignKey(
                        limit_choices_to={"role": "client"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="devis",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="devis",
                        to="api.service",
                    ),
                ),
            ],
            options={
                "verbose_name": "Devis",
                "verbose_name_plural": "Devis",
            },
        ),
        migrations.CreateModel(
            name="PanierProduit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantite",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(1)]
                    ),
                ),
                ("date_ajout", models.DateTimeField(auto_now_add=True)),
                (
                    "panier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="api.panier",
                    ),
                ),
                (
                    "produit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paniers",
                        to="api.produit",
                    ),
                ),
            ],
            options={
                "verbose_name": "Produit du panier",
                "verbose_name_plural": "Produits du panier",
                "unique_together": {("panier", "produit")},
            },
        ),
    ]


# --- api\migrations\0002_remove_paiement_id_transaction_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-01 14:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="paiement",
            name="id_transaction",
        ),
        migrations.AddField(
            model_name="abonnement",
            name="prochaine_livraison",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="abonnement",
            name="produits",
            field=models.ManyToManyField(
                help_text="Produits inclus dans l'abonnement",
                related_name="abonnements",
                to="api.produit",
            ),
        ),
        migrations.AddField(
            model_name="paiement",
            name="abonnement",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="paiements",
                to="api.abonnement",
            ),
        ),
        migrations.AddField(
            model_name="paiement",
            name="atelier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="paiements",
                to="api.atelier",
            ),
        ),
        migrations.AddField(
            model_name="paiement",
            name="commande",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="paiements",
                to="api.commande",
            ),
        ),
        migrations.CreateModel(
            name="OTP",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(default="868630", max_length=6)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("expiration", models.DateTimeField()),
                ("is_used", models.BooleanField(default=False)),
                (
                    "utilisateur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="otps",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "OTP",
                "verbose_name_plural": "OTPs",
            },
        ),
    ]


# --- api\migrations\0003_alter_otp_code.py ---

# Generated by Django 5.1.3 on 2025-03-01 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_remove_paiement_id_transaction_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="code",
            field=models.CharField(default="951586", max_length=6),
        ),
    ]


# --- api\migrations\0004_alter_otp_code.py ---

# Generated by Django 5.1.3 on 2025-03-01 16:06

import api.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_alter_otp_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="code",
            field=models.CharField(default=api.models.generate_otp_code, max_length=6),
        ),
    ]


# --- api\migrations\0005_utilisateur_is_banned_alter_utilisateur_adresse_and_more.py ---

# Generated by Django 5.1.6 on 2025-03-01 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_alter_otp_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="utilisateur",
            name="is_banned",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="utilisateur",
            name="adresse",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="utilisateur",
            name="role",
            field=models.CharField(
                choices=[("client", "Client"), ("admin", "Administrateur")],
                default="client",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="utilisateur",
            name="telephone",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]


# --- api\migrations\0006_alter_utilisateur_is_active.py ---

# Generated by Django 5.1.6 on 2025-03-02 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_utilisateur_is_banned_alter_utilisateur_adresse_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="utilisateur",
            name="is_active",
            field=models.BooleanField(default=False),
        ),
    ]


# --- api\migrations\0007_produit_prix_reduit.py ---

# Generated by Django 5.1.6 on 2025-03-02 21:15

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0006_alter_utilisateur_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="produit",
            name="prix_reduit",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
    ]


# --- api\migrations\0008_remove_produit_prix_reduit.py ---

# Generated by Django 5.1.6 on 2025-03-02 21:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_produit_prix_reduit"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="produit",
            name="prix_reduit",
        ),
    ]


# --- api\migrations\0009_adresse_commande_adresse.py ---

# Generated by Django 5.1.3 on 2025-03-03 20:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_remove_produit_prix_reduit"),
    ]

    operations = [
        migrations.CreateModel(
            name="Adresse",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=100)),
                ("rue", models.CharField(max_length=200)),
                ("ville", models.CharField(max_length=100)),
                ("code_postal", models.CharField(max_length=20)),
                ("pays", models.CharField(max_length=100)),
                ("is_default", models.BooleanField(default=False)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="adresses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="commande",
            name="adresse",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.adresse",
            ),
        ),
    ]


# --- api\migrations\0010_wishlist.py ---

# Generated by Django 5.1.3 on 2025-03-04 12:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_adresse_commande_adresse"),
    ]

    operations = [
        migrations.CreateModel(
            name="Wishlist",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_mise_a_jour", models.DateTimeField(auto_now=True)),
                (
                    "client",
                    models.ForeignKey(
                        limit_choices_to={"role": "client"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlist",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "produits",
                    models.ManyToManyField(
                        blank=True, related_name="wishlists", to="api.produit"
                    ),
                ),
            ],
            options={
                "verbose_name": "Liste de souhaits",
                "verbose_name_plural": "Listes de souhaits",
                "unique_together": {("client",)},
            },
        ),
    ]


# --- api\migrations\0011_rename_admin_article_auteur_article_cover.py ---

# Generated by Django 5.1.3 on 2025-03-04 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_wishlist"),
    ]

    operations = [
        migrations.RenameField(
            model_name="article",
            old_name="admin",
            new_name="auteur",
        ),
        migrations.AddField(
            model_name="article",
            name="cover",
            field=models.ImageField(blank=True, null=True, upload_to="article_covers"),
        ),
    ]


# --- api\migrations\0012_commentaire_parent.py ---

# Generated by Django 5.1.3 on 2025-03-04 15:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_rename_admin_article_auteur_article_cover"),
    ]

    operations = [
        migrations.AddField(
            model_name="commentaire",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reponses",
                to="api.commentaire",
            ),
        ),
    ]


# --- api\migrations\0013_alter_article_auteur_alter_article_titre_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-04 16:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0012_commentaire_parent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="auteur",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="article",
            name="titre",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="commentaire",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]


# --- api\migrations\0014_alter_commande_statut.py ---

# Generated by Django 5.1.3 on 2025-03-05 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0013_alter_article_auteur_alter_article_titre_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="commande",
            name="statut",
            field=models.CharField(
                choices=[
                    ("en_attente", "En attente"),
                    ("en_cours", "En cours"),
                    ("expediee", "Expédiée"),
                    ("livree", "Livrée"),
                    ("annulee", "Annulée"),
                ],
                default="en_attente_paiement",
                max_length=20,
            ),
        ),
    ]


# --- api\migrations\0015_alter_atelier_options_remove_atelier_date_creation_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-06 07:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0014_alter_commande_statut"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="atelier",
            options={},
        ),
        migrations.RemoveField(
            model_name="atelier",
            name="date_creation",
        ),
        migrations.RemoveField(
            model_name="atelier",
            name="participants",
        ),
        migrations.RemoveField(
            model_name="atelier",
            name="places_disponibles",
        ),
        migrations.RemoveField(
            model_name="atelier",
            name="titre",
        ),
        migrations.AddField(
            model_name="atelier",
            name="duree",
            field=models.IntegerField(default=0, help_text="Durée en minutes"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="atelier",
            name="nom",
            field=models.CharField(default="atelier", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="atelier",
            name="places_totales",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="atelier",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="atelier",
            name="prix",
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.CreateModel(
            name="Participant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_inscription", models.DateTimeField(auto_now_add=True)),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("inscrit", "Inscrit"),
                            ("present", "Présent"),
                            ("annule", "Annulé"),
                        ],
                        default="inscrit",
                        max_length=20,
                    ),
                ),
                (
                    "atelier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participants",
                        to="api.atelier",
                    ),
                ),
                (
                    "utilisateur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("atelier", "utilisateur")},
            },
        ),
    ]


# --- api\migrations\0016_paiement_date_creation_paiement_methode_paiement.py ---

# Generated by Django 5.1.3 on 2025-03-06 10:31

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0015_alter_atelier_options_remove_atelier_date_creation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="paiement",
            name="date_creation",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="paiement",
            name="methode_paiement",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]


# --- api\migrations\0017_remove_produit_photos_remove_realisation_photos_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-11 14:46

import api.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0016_paiement_date_creation_paiement_methode_paiement"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="produit",
            name="photos",
        ),
        migrations.RemoveField(
            model_name="realisation",
            name="photos",
        ),
        migrations.RemoveField(
            model_name="service",
            name="photos",
        ),
        migrations.AlterField(
            model_name="otp",
            name="code",
            field=models.CharField(default=api.models.generate_otp_code, max_length=20),
        ),
        migrations.CreateModel(
            name="Photo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        help_text="Image au format JPG, JPEG, PNG ou GIF, max 5MB",
                        upload_to="photos/%Y/%m/%d/",
                        validators=[api.models.validate_image],
                    ),
                ),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "produit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="photos",
                        to="api.produit",
                    ),
                ),
                (
                    "realisation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="photos",
                        to="api.realisation",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="photos",
                        to="api.service",
                    ),
                ),
            ],
            options={
                "verbose_name": "Photo",
                "verbose_name_plural": "Photos",
            },
        ),
        migrations.AddField(
            model_name="article",
            name="photos",
            field=models.ManyToManyField(
                blank=True, related_name="articles", to="api.photo"
            ),
        ),
    ]


# --- api\migrations\0018_rename_places_totales_atelier_places_disponibles.py ---

# Generated by Django 5.1.3 on 2025-03-13 12:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0017_remove_produit_photos_remove_realisation_photos_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="atelier",
            old_name="places_totales",
            new_name="places_disponibles",
        ),
    ]


# --- api\migrations\0019_atelier_places_totales.py ---

# Generated by Django 5.1.3 on 2025-03-13 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0018_rename_places_totales_atelier_places_disponibles"),
    ]

    operations = [
        migrations.AddField(
            model_name="atelier",
            name="places_totales",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]


# --- api\migrations\0020_alter_abonnement_options_remove_abonnement_produits_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-23 21:32

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0019_atelier_places_totales"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="abonnement",
            options={},
        ),
        migrations.RemoveField(
            model_name="abonnement",
            name="produits",
        ),
        migrations.AlterField(
            model_name="abonnement",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="abonnements",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="AbonnementProduit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantite",
                    models.IntegerField(
                        default=1,
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "abonnement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="abonnement_produits",
                        to="api.abonnement",
                    ),
                ),
                (
                    "produit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="api.produit"
                    ),
                ),
            ],
            options={
                "verbose_name": "Produit d'abonnement",
                "verbose_name_plural": "Produits d'abonnement",
                "unique_together": {("abonnement", "produit")},
            },
        ),
    ]


# --- api\migrations\0021_remove_abonnement_date_creation_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-23 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0020_alter_abonnement_options_remove_abonnement_produits_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="abonnement",
            name="date_creation",
        ),
        migrations.RemoveField(
            model_name="abonnement",
            name="date_mise_a_jour",
        ),
        migrations.AddField(
            model_name="abonnement",
            name="paiement_statut",
            field=models.CharField(
                choices=[
                    ("non_paye", "Non payé"),
                    ("paye_complet", "Payé en une fois"),
                    ("paye_mensuel", "Payé mensuellement"),
                ],
                default="non_paye",
                max_length=20,
            ),
        ),
    ]


# --- api\migrations\0022_abonnement_prochaine_facturation_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-23 22:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0021_remove_abonnement_date_creation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="abonnement",
            name="prochaine_facturation",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="abonnement",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name="abonnement",
            name="prix",
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]


# --- api\migrations\0023_abonnement_date_creation.py ---

# Generated by Django 5.1.3 on 2025-03-23 22:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0022_abonnement_prochaine_facturation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="abonnement",
            name="date_creation",
            field=models.DateField(auto_now=True),
        ),
    ]


# --- api\migrations\0024_abonnement_date_mise_a_jour.py ---

# Generated by Django 5.1.3 on 2025-03-23 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0023_abonnement_date_creation"),
    ]

    operations = [
        migrations.AddField(
            model_name="abonnement",
            name="date_mise_a_jour",
            field=models.DateField(auto_now=True),
        ),
    ]


# --- api\migrations\0025_alter_abonnement_prix.py ---

# Generated by Django 5.1.3 on 2025-03-23 23:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0024_abonnement_date_mise_a_jour"),
    ]

    operations = [
        migrations.AlterField(
            model_name="abonnement",
            name="prix",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]


# --- api\migrations\0026_alter_abonnement_options_alter_adresse_options_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-24 16:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0025_alter_abonnement_prix"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="abonnement",
            options={"ordering": ["id"]},
        ),
        migrations.AlterModelOptions(
            name="adresse",
            options={"ordering": ["id"]},
        ),
        migrations.AlterModelOptions(
            name="article",
            options={
                "ordering": ["id"],
                "verbose_name": "Article",
                "verbose_name_plural": "Articles",
            },
        ),
        migrations.AlterModelOptions(
            name="categorie",
            options={
                "ordering": ["id"],
                "verbose_name": "Catégorie",
                "verbose_name_plural": "Catégories",
            },
        ),
        migrations.AlterModelOptions(
            name="commande",
            options={
                "ordering": ["id"],
                "verbose_name": "Commande",
                "verbose_name_plural": "Commandes",
            },
        ),
        migrations.AlterModelOptions(
            name="commentaire",
            options={
                "ordering": ["id"],
                "verbose_name": "Commentaire",
                "verbose_name_plural": "Commentaires",
            },
        ),
        migrations.AlterModelOptions(
            name="devis",
            options={
                "ordering": ["id"],
                "verbose_name": "Devis",
                "verbose_name_plural": "Devis",
            },
        ),
        migrations.AlterModelOptions(
            name="lignecommande",
            options={
                "ordering": ["id"],
                "verbose_name": "Ligne de commande",
                "verbose_name_plural": "Lignes de commande",
            },
        ),
        migrations.AlterModelOptions(
            name="otp",
            options={
                "ordering": ["id"],
                "verbose_name": "OTP",
                "verbose_name_plural": "OTPs",
            },
        ),
        migrations.AlterModelOptions(
            name="panier",
            options={
                "ordering": ["id"],
                "verbose_name": "Panier",
                "verbose_name_plural": "Paniers",
            },
        ),
        migrations.AlterModelOptions(
            name="panierproduit",
            options={
                "ordering": ["id"],
                "verbose_name": "Produit du panier",
                "verbose_name_plural": "Produits du panier",
            },
        ),
        migrations.AlterModelOptions(
            name="parametre",
            options={
                "ordering": ["id"],
                "verbose_name": "Paramètre",
                "verbose_name_plural": "Paramètres",
            },
        ),
        migrations.AlterModelOptions(
            name="participant",
            options={"ordering": ["id"]},
        ),
        migrations.AlterModelOptions(
            name="photo",
            options={
                "ordering": ["id"],
                "verbose_name": "Photo",
                "verbose_name_plural": "Photos",
            },
        ),
        migrations.AlterModelOptions(
            name="produit",
            options={
                "ordering": ["id"],
                "verbose_name": "Produit",
                "verbose_name_plural": "Produits",
            },
        ),
        migrations.AlterModelOptions(
            name="promotion",
            options={
                "ordering": ["id"],
                "verbose_name": "Promotion",
                "verbose_name_plural": "Promotions",
            },
        ),
        migrations.AlterModelOptions(
            name="realisation",
            options={
                "ordering": ["id"],
                "verbose_name": "Réalisation",
                "verbose_name_plural": "Réalisations",
            },
        ),
        migrations.AlterModelOptions(
            name="service",
            options={
                "ordering": ["id"],
                "verbose_name": "Service",
                "verbose_name_plural": "Services",
            },
        ),
        migrations.AlterModelOptions(
            name="utilisateur",
            options={
                "ordering": ["id"],
                "verbose_name": "Utilisateur",
                "verbose_name_plural": "Utilisateurs",
            },
        ),
        migrations.AlterModelOptions(
            name="wishlist",
            options={
                "ordering": ["id"],
                "verbose_name": "Liste de souhaits",
                "verbose_name_plural": "Listes de souhaits",
            },
        ),
    ]


# --- api\migrations\0027_alter_devis_options_remove_devis_date_demande_and_more.py ---

# Generated by Django 5.1.3 on 2025-03-25 07:56

import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0026_alter_abonnement_options_alter_adresse_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="devis",
            options={
                "ordering": ["-date_creation"],
                "verbose_name": "Devis",
                "verbose_name_plural": "Devis",
            },
        ),
        migrations.RemoveField(
            model_name="devis",
            name="date_demande",
        ),
        migrations.AddField(
            model_name="devis",
            name="commentaire_admin",
            field=models.TextField(
                blank=True,
                help_text="Commentaire ou justification de l'admin (ex. raison du refus).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="devis",
            name="date_creation",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                help_text="Date de création du devis.",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="devis",
            name="date_expiration",
            field=models.DateTimeField(
                blank=True,
                help_text="Date limite pour accepter/refuser le devis.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="devis",
            name="date_soumission",
            field=models.DateTimeField(
                blank=True, help_text="Date de soumission à l'admin.", null=True
            ),
        ),
        migrations.AddField(
            model_name="devis",
            name="prix_demande",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Prix demandé par le client (facultatif).",
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name="devis",
            name="date_mise_a_jour",
            field=models.DateTimeField(
                auto_now=True, help_text="Dernière mise à jour du devis."
            ),
        ),
        migrations.AlterField(
            model_name="devis",
            name="description",
            field=models.TextField(
                help_text="Description détaillée de la demande du client."
            ),
        ),
        migrations.AlterField(
            model_name="devis",
            name="is_active",
            field=models.BooleanField(
                default=True, help_text="Indique si le devis est actif ou archivé."
            ),
        ),
        migrations.AlterField(
            model_name="devis",
            name="prix_propose",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Prix proposé par l'admin.",
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name="devis",
            name="statut",
            field=models.CharField(
                choices=[
                    ("brouillon", "Brouillon"),
                    ("soumis", "Soumis"),
                    ("en_cours", "En cours"),
                    ("accepte", "Accepté"),
                    ("refuse", "Refusé"),
                    ("expire", "Expiré"),
                ],
                default="brouillon",
                help_text="État actuel du devis.",
                max_length=20,
            ),
        ),
    ]


# --- api\migrations\__init__.py ---



# --- api\tests\test_utilisateur.py ---

import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from api.models import Utilisateur, OTP
from django.utils import timezone

@pytest.fixture
def client():
    """Fixture pour créer un client API de test."""
    return APIClient()

@pytest.fixture
def user(db):
    """Fixture pour créer un utilisateur de test dans la base de données."""
    return Utilisateur.objects.create_user(username='testuser', email='test@example.com', password='test123')

@pytest.mark.django_db
def test_register_user(client):
    """Teste l’inscription d’un nouvel utilisateur via l’endpoint /register/."""
    url = reverse('register')  # Nécessite que 'register' soit nommé dans urls.py
    data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpass123'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 201
    assert response.data['status'] == 'Utilisateur créé, OTP envoyé par email'
    assert Utilisateur.objects.filter(username='newuser').exists()
    assert OTP.objects.filter(utilisateur__username='newuser').exists()

@pytest.mark.django_db
def test_verify_otp(client, user):
    """Teste la vérification d’un OTP pour activer un compte utilisateur."""
    otp = OTP.objects.create(
        utilisateur=user,
        code='123456',
        expiration=timezone.now() + timezone.timedelta(minutes=10)
    )
    url = reverse('verify-otp')  # Nécessite que 'verify-otp' soit nommé dans urls.py
    data = {'user_id': user.id, 'code': '123456'}
    response = client.post(url, data, format='json')
    assert response.status_code == 200
    assert response.data['status'] == 'Compte activé'
    user.refresh_from_db()
    assert user.is_active is True
    otp.refresh_from_db()
    assert otp.is_used is True

@pytest.mark.django_db
def test_me_authenticated(client, user):
    """Teste la récupération des informations de l’utilisateur connecté via /me/."""
    client.force_authenticate(user=user)
    url = reverse('utilisateur-me')  # Nécessite que 'utilisateur-me' soit nommé dans urls.py
    response = client.get(url)
    assert response.status_code == 200
    assert response.data['username'] == 'testuser'

# --- api\tests\__init__.py ---



# --- chezflora_api\asgi.py ---

"""
ASGI config for chezflora_api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chezflora_api.settings")

application = get_asgi_application()


# --- chezflora_api\celery.py ---

# chezflora_api/celery.py

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chezflora_api.settings')

app = Celery('chezflora_api')

# Charger la configuration depuis Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches dans tes apps Django
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Requête : {self.request!r}')


# --- chezflora_api\settings.py ---

"""
Django settings for chezflora_api project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-+1okhughn%s^+=fkn2bd^*3c$%ozs&rg2&$i7$5e-(9@*)mt#^"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', 'chezflora-api.onrender.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders', # temporaire pour les besoins de developpement
    'django_filters',
    'rest_framework',  # Ajout de DRF
    'rest_framework_simplejwt',
    'drf_spectacular',
    'api',  # Ajout de votre application
    'django_celery_beat'
]

AUTH_USER_MODEL = 'api.Utilisateur'

# Configurez Simple JWT comme méthode d'authentification par défaut
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100000/day',
        'user': '100000/day',
        'register': '5/hour',
        'verify_otp': '10/hour',
    },
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'SEARCH_PARAM': 'search',
    'ORDERING_PARAM': 'ordering',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',  # Ajout du handler personnalisé
}

# Configuration de drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'ChezFlora API',
    'DESCRIPTION': 'API pour la gestion de ChezFlora : produits, commandes, abonnements, ateliers, et plus.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': True,  # Inclure le schéma dans Swagger UI
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': 1,
    },
    'COMPONENT_SPLIT_REQUEST': True,  # Séparer les requêtes GET et POST dans l'UI
}

# Configuration des tokens JWT
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=180),  # Durée de vie du token d'accès
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),    # Durée de vie du token de rafraîchissement
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # temporaire pour des besoins de developpement
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')

CORS_ALLOW_CREDENTIALS = True  # Pour les cookies/auth


ROOT_URLCONF = "chezflora_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'api' / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "chezflora_api.wsgi.application"

from decouple import config

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST'),
#         'PORT': config('DB_PORT', default='5432', cast=int),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chezflora_db',
        'USER': 'neondb_owner',
        'PASSWORD': 'npg_3Gc8QLlUVEPR',
        'HOST': 'ep-lingering-heart-a5x1cyzz-pooler.us-east-2.aws.neon.tech',
        'PORT': 5432,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Static et Media
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Paramètres d'email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'plazarecrute@gmail.com'  # Votre adresse Gmail
EMAIL_HOST_PASSWORD = 'pwwnirrsryrdbtcb'          # votre mot de passe d’application
DEFAULT_FROM_EMAIL = 'ChezFlora <plazarecrute@gmail.com>'

CONTACT_EMAIL = 'emmanuelscre1@gmail.com'

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

from celery.schedules import crontab
# Celery Beat Configuration
CELERY_BEAT_SCHEDULE = {
    # Génération des commandes d'abonnements toutes les heures
    'generer-commandes-abonnements-toutes-les-heures': {
        'task': 'api.tasks.generer_commandes_abonnements',
        'schedule': 3600.0,  # Toutes les heures (en secondes)
    },
    # Facturation des abonnements tous les jours à minuit
    'facturer-abonnements-quotidien': {
        'task': 'api.tasks.facturer_abonnements',
        'schedule': crontab(hour=0, minute=0),  # Tous les jours à 00:00
    },
    # Notification de stock faible tous les jours à 8h00
    'notifier-stock-faible-quotidien': {
        'task': 'api.tasks.notifier_stock_faible',
        'schedule': crontab(hour=8, minute=0),  # Tous les jours à 08:00
    },
    # Sauvegarde de la base de données tous les jours à 2h00
    'backup-database-quotidien': {
        'task': 'api.tasks.backup_database',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 02:00
    },
    # Sauvegarde des fichiers médias tous les jours à 3h00
    'backup-media-quotidien': {
        'task': 'api.tasks.backup_media_files',
        'schedule': crontab(hour=3, minute=0),  # Tous les jours à 03:00
    },
}


# Configuration du cache avec Redis
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',  # Base 1 pour le cache, Celery utilise 0
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# Durée par défaut du cache (en secondes, ici 5 minutes)
CACHE_TTL = 60 * 5  # 300 secondes



# --- chezflora_api\urls.py ---

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

from api.views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Endpoints pour Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # Schéma brut
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # Interface Swagger
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# --- chezflora_api\wsgi.py ---

"""
WSGI config for chezflora_api project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chezflora_api.settings")

application = get_wsgi_application()


# --- chezflora_api\__init__.py ---

from .celery import app as celery_app
__all__ = ('celery_app',)

