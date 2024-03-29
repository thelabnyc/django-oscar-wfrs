# Generated by Django 2.2 on 2019-04-01 16:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0027_auto_20190208_1635"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cacreditapp",
            name="status",
            field=models.CharField(
                choices=[
                    ("", "Unknown"),
                    ("E0", "Approved"),
                    ("E1", "Pending"),
                    ("E2", "Format Error"),
                    ("E3", "Wells Fargo Error"),
                    ("E4", "Denied"),
                ],
                default="",
                max_length=2,
                verbose_name="Application Status",
            ),
        ),
        migrations.AlterField(
            model_name="cajointcreditapp",
            name="status",
            field=models.CharField(
                choices=[
                    ("", "Unknown"),
                    ("E0", "Approved"),
                    ("E1", "Pending"),
                    ("E2", "Format Error"),
                    ("E3", "Wells Fargo Error"),
                    ("E4", "Denied"),
                ],
                default="",
                max_length=2,
                verbose_name="Application Status",
            ),
        ),
        migrations.AlterField(
            model_name="uscreditapp",
            name="status",
            field=models.CharField(
                choices=[
                    ("", "Unknown"),
                    ("E0", "Approved"),
                    ("E1", "Pending"),
                    ("E2", "Format Error"),
                    ("E3", "Wells Fargo Error"),
                    ("E4", "Denied"),
                ],
                default="",
                max_length=2,
                verbose_name="Application Status",
            ),
        ),
        migrations.AlterField(
            model_name="usjointcreditapp",
            name="status",
            field=models.CharField(
                choices=[
                    ("", "Unknown"),
                    ("E0", "Approved"),
                    ("E1", "Pending"),
                    ("E2", "Format Error"),
                    ("E3", "Wells Fargo Error"),
                    ("E4", "Denied"),
                ],
                default="",
                max_length=2,
                verbose_name="Application Status",
            ),
        ),
    ]
