# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-10-17 23:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wellsfargo', '0009_auto_20171005_1541'),
    ]

    operations = [
        migrations.AddField(
            model_name='fraudscreenresult',
            name='reference',
            field=models.CharField(default='', max_length=128, verbose_name='Reference'),
            preserve_default=False,
        ),
    ]