# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-02 23:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0016_prequalificationresponse_customer_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="accountinquiryresult",
            name="prequal_response_source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="account_inquiries",
                to="wellsfargo.PreQualificationResponse",
                verbose_name="Pre-Qualification Source",
            ),
        ),
        migrations.AlterField(
            model_name="accountinquiryresult",
            name="address",
            field=models.CharField(max_length=100, verbose_name="Address Line 1"),
        ),
        migrations.AlterField(
            model_name="accountinquiryresult",
            name="status",
            field=models.CharField(
                choices=[
                    ("I0", "Account Inquiry Succeeded"),
                    ("I1", "Could Not Find Requested Account"),
                    ("I2", "Wells Fargo System Error"),
                    ("H0", "OTB Success"),
                    ("H1", "OTB Failed"),
                    ("H2", "OTB No Match"),
                    ("H3", "OTB Account Not Found"),
                    ("H4", "OTB Denied"),
                    ("H5", "OTB External Status Code"),
                ],
                max_length=2,
                verbose_name="Status",
            ),
        ),
    ]
