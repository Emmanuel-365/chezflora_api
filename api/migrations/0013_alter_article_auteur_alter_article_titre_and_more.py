# Generated by Django 5.1.3 on 2025-03-04 16:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0012_commentaire_parent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="auteur",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="article",
            name="titre",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="commentaire",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
