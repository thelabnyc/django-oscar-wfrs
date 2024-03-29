# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-01-02 16:47
from __future__ import unicode_literals

from django.db import migrations
import oscar.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0011_auto_20171204_1506"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cacreditapp",
            name="main_cell_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Cell Phone"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cacreditapp",
            name="main_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cacreditapp",
            name="main_home_phone",
            field=oscar.models.fields.PhoneNumberField(verbose_name="Home Phone"),
        ),
        migrations.AlterField(
            model_name="cajointcreditapp",
            name="joint_cell_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Cell Phone"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cajointcreditapp",
            name="joint_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cajointcreditapp",
            name="main_cell_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Cell Phone"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cajointcreditapp",
            name="main_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cajointcreditapp",
            name="main_home_phone",
            field=oscar.models.fields.PhoneNumberField(verbose_name="Home Phone"),
        ),
        migrations.AlterField(
            model_name="uscreditapp",
            name="main_cell_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Cell Phone"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="uscreditapp",
            name="main_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="uscreditapp",
            name="main_home_phone",
            field=oscar.models.fields.PhoneNumberField(verbose_name="Home Phone"),
        ),
        migrations.AlterField(
            model_name="usjointcreditapp",
            name="joint_cell_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Cell Phone"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="usjointcreditapp",
            name="joint_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="usjointcreditapp",
            name="main_cell_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Cell Phone"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="usjointcreditapp",
            name="main_employer_phone",
            field=oscar.models.fields.PhoneNumberField(
                blank=True, null=True, verbose_name="Employer Phone Number"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="usjointcreditapp",
            name="main_home_phone",
            field=oscar.models.fields.PhoneNumberField(verbose_name="Home Phone"),
        ),
    ]
