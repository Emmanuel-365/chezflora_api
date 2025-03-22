from celery import shared_task
from .models import Abonnement, Produit, Utilisateur
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@shared_task
def generer_commandes_abonnements():
    abonnements = Abonnement.objects.filter(is_active=True, prochaine_livraison__lte=timezone.now())
    for abonnement in abonnements:
        abonnement.generer_commande()
    return f"{len(abonnements)} commandes générées"

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