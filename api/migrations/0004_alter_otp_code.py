# Generated by Django 5.1.3 on 2025-03-01 16:06

import api.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_alter_otp_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="code",
            field=models.CharField(default=api.models.generate_otp_code, max_length=6),
        ),
    ]
