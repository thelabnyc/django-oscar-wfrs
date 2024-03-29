# Generated by Django 2.2.3 on 2019-07-19 22:29

import django.contrib.postgres.fields.citext
import django.contrib.postgres.search
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0030_auto_20190719_1500"),
    ]

    operations = [
        migrations.CreateModel(
            name="CreditAppIndex",
            fields=[
                ("app_type_code", models.CharField(max_length=15)),
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("merchant_name", models.CharField(max_length=200)),
                ("status", models.CharField(max_length=2)),
                ("application_source", models.CharField(max_length=25)),
                ("modified_datetime", models.DateTimeField()),
                ("created_datetime", models.DateTimeField()),
                ("account_number", models.CharField(max_length=16, null=True)),
                ("purchase_price", models.IntegerField(null=True)),
                (
                    "main_first_name",
                    django.contrib.postgres.fields.citext.CICharField(max_length=15),
                ),
                (
                    "main_last_name",
                    django.contrib.postgres.fields.citext.CICharField(max_length=20),
                ),
                (
                    "email",
                    django.contrib.postgres.fields.citext.CIEmailField(max_length=254),
                ),
                (
                    "joint_first_name",
                    django.contrib.postgres.fields.citext.CICharField(max_length=15),
                ),
                (
                    "joint_last_name",
                    django.contrib.postgres.fields.citext.CICharField(max_length=20),
                ),
                (
                    "user_full_name",
                    django.contrib.postgres.fields.citext.CICharField(max_length=200),
                ),
                (
                    "user_username",
                    django.contrib.postgres.fields.citext.CICharField(
                        max_length=150, null=True
                    ),
                ),
                (
                    "submitting_user_full_name",
                    django.contrib.postgres.fields.citext.CICharField(max_length=200),
                ),
                (
                    "submitting_user_username",
                    django.contrib.postgres.fields.citext.CICharField(
                        max_length=150, null=True
                    ),
                ),
                ("name", django.contrib.postgres.search.SearchVectorField()),
                ("address", django.contrib.postgres.search.SearchVectorField()),
                ("phone", django.contrib.postgres.search.SearchVectorField()),
                ("text", django.contrib.postgres.search.SearchVectorField()),
            ],
            options={
                "managed": False,
            },
        ),
    ]
