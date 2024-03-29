# Generated by Django 2.1.2 on 2018-11-05 20:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0019_prequalificationrequest_customer_initiated"),
    ]

    operations = [
        migrations.CreateModel(
            name="PreQualificationSDKApplicationResult",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "application_id",
                    models.CharField(max_length=8, verbose_name="Unique Response ID"),
                ),
                (
                    "first_name",
                    models.CharField(max_length=15, verbose_name="First Name"),
                ),
                (
                    "last_name",
                    models.CharField(max_length=20, verbose_name="Last Name"),
                ),
                (
                    "application_status",
                    models.CharField(max_length=20, verbose_name="Application Status"),
                ),
                ("created_datetime", models.DateTimeField(auto_now_add=True)),
                ("modified_datetime", models.DateTimeField(auto_now=True)),
                (
                    "prequal_response",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sdk_application_result",
                        to="wellsfargo.PreQualificationResponse",
                        verbose_name="PreQualification Response",
                    ),
                ),
            ],
        ),
    ]
