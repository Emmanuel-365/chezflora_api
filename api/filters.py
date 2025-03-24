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