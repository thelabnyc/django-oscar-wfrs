# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-10-02 21:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0004_auto_20160111_1108"),
        ("wellsfargo", "0007_financingplan_advertising_enabled"),
    ]

    operations = [
        migrations.CreateModel(
            name="FraudScreenResult",
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
                    "screen_type",
                    models.CharField(max_length=25, verbose_name="Fraud Screen Type"),
                ),
                (
                    "decision",
                    models.CharField(
                        choices=[
                            ("REJECT", "Transaction was rejected"),
                            ("ACCEPT", "Transaction was accepted"),
                            ("ERROR", "Error occurred while running fraud screen"),
                        ],
                        max_length=25,
                        verbose_name="Decision",
                    ),
                ),
                ("message", models.TextField(verbose_name="Message")),
                ("created_datetime", models.DateTimeField(auto_now_add=True)),
                ("modified_datetime", models.DateTimeField(auto_now=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="order.Order"
                    ),
                ),
            ],
            options={
                "ordering": ("-created_datetime", "-id"),
            },
        ),
    ]
