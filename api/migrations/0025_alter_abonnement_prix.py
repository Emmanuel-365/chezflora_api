# Generated by Django 5.1.3 on 2025-03-23 23:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0024_abonnement_date_mise_a_jour"),
    ]

    operations = [
        migrations.AlterField(
            model_name="abonnement",
            name="prix",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
