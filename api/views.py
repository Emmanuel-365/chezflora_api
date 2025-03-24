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
        elif instance.categorie:
            instance.produits.set(Produit.objects.filter(categorie=instance.categorie))
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
            commande.save()
            Paiement.objects.create(commande=commande, type_transaction='commande', montant=total)
            panier.items.all().delete()

        return Response({'status': 'Commande créée et paiement simulé', 'commande_id': commande.id}, status=status.HTTP_201_CREATED)


# ViewSet pour les devis (authentification requise)
class DevisViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les devis. Nécessite une authentification.
    """
    serializer_class = DevisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DevisFilter
    search_fields = ['description']
    ordering_fields = ['date_demande']
    pagination_class = StandardResultsSetPagination  # Ajouté

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Devis.objects.none()
        if self.request.user.role == 'admin':
            return Devis.objects.all()
        return Devis.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    def perform_update(self, serializer):
        devis = serializer.save()
        if 'prix_propose' in serializer.validated_data or 'statut' in serializer.validated_data:
            subject = 'Réponse à votre devis - ChezFlora'
            html_message = render_to_string('devis_reponse_email.html', {
                'client_name': devis.client.username,
                'service': devis.service.nom,
                'prix_propose': devis.prix_propose or 'N/A',
                'statut': devis.statut,
            })
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message, 'ChezFlora <plazarecrute@gmail.com>', [devis.client.email], html_message=html_message)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def proposer_prix(self, request, pk=None):
        devis = self.get_object()
        prix_propose = request.data.get('prix_propose')
        statut = request.data.get('statut', 'en_attente')

        if prix_propose is None:
            return Response({'error': 'Le prix proposé est requis.'}, status=400)

        devis.prix_propose = Decimal(prix_propose)
        devis.statut = statut if statut in ['accepte', 'refuse'] else 'en_attente'
        devis.save()

        # Simulation d'une notification (à remplacer par un vrai système d'email/notification)
        print(f"Notification à {devis.client.email}: Votre devis pour {devis.service.nom} a été mis à jour à {prix_propose}€ - Statut: {devis.statut}")

        return Response({'status': 'Prix proposé et statut mis à jour', 'devis_id': devis.id})

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