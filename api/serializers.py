from django.utils import timezone
from decimal import Decimal
from rest_framework import serializers
from .models import (
    Utilisateur, Categorie, Produit, Promotion, Commande, LigneCommande, Photo,
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
            date_debut__lte=timezone.now(),  # Utilisez timezone.now() ici
            date_fin__gte=timezone.now()     # Utilisez timezone.now() ici
        )
        if promotions.exists():
            reduction = max(p.reduction for p in promotions)
            return float(obj.prix) * float(1 - reduction)
        return float(obj.prix)
    
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
    produit_ids = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all(), many=True, source='produits', write_only=True, required=False)

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

# Serializer pour Devis
class DevisSerializer(serializers.ModelSerializer):
    # client = UtilisateurSerializer(read_only=True)
    # client_id = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.filter(role='client'), source='client', write_only=True)
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), read_only=False)

    class Meta:
        model = Devis
        fields = ['id', 'service', 'description', 'date_demande', 'statut', 'prix_propose', 'is_active', 'date_mise_a_jour']
        read_only_fields = ['date_demande', 'date_mise_a_jour']

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

# Serializer pour Abonnement
class AbonnementSerializer(serializers.ModelSerializer):
    produits = ProduitSerializer(many=True, read_only=True)
    produit_ids = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        many=True,
        source='produits',
        write_only=True
    )
    prix = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Abonnement
        fields = ['id', 'type', 'date_debut', 'date_fin', 'produits', 'produit_ids', 
                  'prix', 'is_active', 'date_creation', 'date_mise_a_jour', 'prochaine_livraison']
        read_only_fields = ['prix', 'date_creation', 'date_mise_a_jour', 'prochaine_livraison']

    def validate(self, data):
        if data.get('date_fin') and data['date_debut'] >= data['date_fin']:
            raise serializers.ValidationError("La date de début doit être antérieure à la date de fin.")
        if not data.get('produits'):
            raise serializers.ValidationError("Un abonnement doit inclure au moins un produit.")
        return data
    
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