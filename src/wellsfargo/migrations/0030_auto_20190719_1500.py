# Generated by Django 2.2.3 on 2019-07-19 19:00

import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0029_auto_20190401_1233"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="accountinquiryresult",
            options={
                "ordering": ("-created_datetime", "-id"),
                "verbose_name": "Account Inquiry Result",
                "verbose_name_plural": "Account Inquiry Results",
            },
        ),
        migrations.AlterModelOptions(
            name="cacreditapp",
            options={
                "verbose_name": "CA Individual Credit Application",
                "verbose_name_plural": "CA Individual Credit Applications",
            },
        ),
        migrations.AlterModelOptions(
            name="cajointcreditapp",
            options={
                "verbose_name": "CA Joint Credit Application",
                "verbose_name_plural": "CA Joint Credit Applications",
            },
        ),
        migrations.AlterModelOptions(
            name="financingplan",
            options={
                "ordering": ("plan_number",),
                "verbose_name": "Financing Plan",
                "verbose_name_plural": "Financing Plans",
            },
        ),
        migrations.AlterModelOptions(
            name="financingplanbenefit",
            options={
                "verbose_name": "Financing Plan Benefit",
                "verbose_name_plural": "Financing Plan Benefits",
            },
        ),
        migrations.AlterModelOptions(
            name="fraudscreenresult",
            options={
                "ordering": ("-created_datetime", "-id"),
                "verbose_name": "Fraud Screen Result",
                "verbose_name_plural": "Fraud Screen Results",
            },
        ),
        migrations.AlterModelOptions(
            name="prequalificationrequest",
            options={
                "ordering": ("-created_datetime", "-id"),
                "verbose_name": "Pre-Qualification Request",
                "verbose_name_plural": "Pre-Qualification Requests",
            },
        ),
        migrations.AlterModelOptions(
            name="prequalificationresponse",
            options={
                "ordering": ("-created_datetime", "-id"),
                "verbose_name": "Pre-Qualification Response",
                "verbose_name_plural": "Pre-Qualification Responses",
            },
        ),
        migrations.AlterModelOptions(
            name="prequalificationsdkapplicationresult",
            options={
                "verbose_name": "Pre-Qualification SDK Application Result",
                "verbose_name_plural": "Pre-Qualification SDK Application Results",
            },
        ),
        migrations.AlterModelOptions(
            name="uscreditapp",
            options={
                "verbose_name": "US Individual Credit Application",
                "verbose_name_plural": "US Individual Credit Applications",
            },
        ),
        migrations.AlterModelOptions(
            name="usjointcreditapp",
            options={
                "verbose_name": "US Joint Credit Application",
                "verbose_name_plural": "US Joint Credit Applications",
            },
        ),
        migrations.AlterField(
            model_name="fraudscreenresult",
            name="created_datetime",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created On"),
        ),
        migrations.AlterField(
            model_name="fraudscreenresult",
            name="modified_datetime",
            field=models.DateTimeField(auto_now=True, verbose_name="Modified On"),
        ),
        migrations.AlterField(
            model_name="fraudscreenresult",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="wfrs_fraud_screen_results",
                to="order.Order",
                verbose_name="Order",
            ),
        ),
        migrations.AlterField(
            model_name="transfermetadata",
            name="created_datetime",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created"),
        ),
        migrations.AlterField(
            model_name="transfermetadata",
            name="modified_datetime",
            field=models.DateTimeField(auto_now=True, verbose_name="Modified"),
        ),
    ]
