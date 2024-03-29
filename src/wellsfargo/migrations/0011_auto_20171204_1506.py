# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-12-04 20:06
from __future__ import unicode_literals

from django.db import migrations
import localflavor.us.models
import wellsfargo.core.fields
import oscar.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0010_fraudscreenresult_reference"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cacreditapp",
            name="main_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
        ),
        migrations.AlterField(
            model_name="cajointcreditapp",
            name="joint_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
        ),
        migrations.AlterField(
            model_name="cajointcreditapp",
            name="main_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
        ),
        migrations.AlterField(
            model_name="uscreditapp",
            name="main_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
        ),
        migrations.AlterField(
            model_name="usjointcreditapp",
            name="joint_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
        ),
        migrations.AlterField(
            model_name="usjointcreditapp",
            name="main_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
        ),
    ]
