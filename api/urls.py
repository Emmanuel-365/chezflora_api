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
]