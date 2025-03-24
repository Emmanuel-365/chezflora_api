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
