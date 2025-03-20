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