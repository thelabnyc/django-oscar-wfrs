# Generated by Django 2.1.4 on 2019-01-25 16:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0022_auto_20181220_1057"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="prequalificationrequest",
            index=models.Index(
                fields=["-created_datetime", "-id"],
                name="wellsfargo__created_99d8f9_idx",
            ),
        ),
    ]
