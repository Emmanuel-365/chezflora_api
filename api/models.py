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
        verbose_name = "Photo"
        verbose_name_plural = "Photos"

    def __str__(self):
        entity = self.produit or self.service or self.realisation
        return f"Photo pour {entity}"

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
        unique_together = ('panier', 'produit')  # Un produit unique par panier
        verbose_name = "Produit du panier"
        verbose_name_plural = "Produits du panier"

    def __str__(self):
        return f"{self.quantite} x {self.produit} dans {self.panier}"

# Modèle Devis
class Devis(models.Model):
    STATUTS = [
        ('en_attente', 'En attente'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
    ]
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='devis', limit_choices_to={'role': 'client'})
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='devis')
    description = models.TextField()
    date_demande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    prix_propose = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Devis"
        verbose_name_plural = "Devis"

    def __str__(self):
        return f"Devis #{self.id} - {self.client} pour {self.service}"

# Modèle Service
class Service(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # Plus de photos = models.JSONField(default=list, blank=True)
    # La relation avec Photo est gérée via related_name='photos'

    class Meta:
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
    prix = models.DecimalField(max_digits=10, decimal_places=2)  # Coût total ou mensuel
    paiement_statut = models.CharField(max_length=20, choices=PAIEMENT_STATUTS, default='non_paye')
    prochaine_facturation = models.DateTimeField(null=True, blank=True)  # Nouvelle date de facturation
    is_active = models.BooleanField(default=True)
    prochaine_livraison = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateField(auto_now=True)

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
        verbose_name = "Liste de souhaits"
        verbose_name_plural = "Listes de souhaits"
        unique_together = ('client',)  # Une seule wishlist par client

    def __str__(self):
        return f"Wishlist de {self.client.username}"