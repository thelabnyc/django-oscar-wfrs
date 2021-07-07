# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-08-21 18:29
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wellsfargo", "0005_financingplan_fine_print_superscript"),
    ]

    operations = [
        migrations.AddField(
            model_name="financingplan",
            name="product_price_threshold",
            field=models.DecimalField(
                decimal_places=2,
                default="0.00",
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                verbose_name="Minimum Product Price for Plan Availability Advertising",
            ),
        ),
    ]
