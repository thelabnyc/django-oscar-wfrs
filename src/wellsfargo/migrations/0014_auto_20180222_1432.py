# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-02-22 19:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellsfargo", "0013_prequalificationrequest_prequalificationresponse"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prequalificationresponse",
            name="customer_response",
            field=models.CharField(
                choices=[
                    ("", ""),
                    ("CLOSE", "Offer Closed"),
                    ("YES", "Offer Accepted"),
                    ("NO", "Offer Rejected"),
                ],
                default="",
                max_length=5,
                verbose_name="Customer Response",
            ),
        ),
    ]
