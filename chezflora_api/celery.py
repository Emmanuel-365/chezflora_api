# chezflora_api/celery.py
import os
from celery import Celery

# Définir les paramètres Django pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chezflora_api.settings')

celery_app = Celery('chezflora_api')

# Charger les paramètres à partir des settings Django
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-détection des tâches dans toutes les apps installées
celery_app.autodiscover_tasks()

@celery_app.task(bind=True)
def debug_task(self):
    print(f'Requête : {self.request!r}')
