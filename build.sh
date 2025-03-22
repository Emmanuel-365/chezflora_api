#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata db_dump.json  # Charge les données
python manage.py collectstatic --noinput