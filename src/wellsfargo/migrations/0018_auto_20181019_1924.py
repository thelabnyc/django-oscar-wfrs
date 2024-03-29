# Generated by Django 2.1.2 on 2018-10-19 23:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0017_auto_20180302_1843"),
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
                    ("SDKPRESENTED", "Offer Presented By PLCCA SDK"),
                ],
                default="",
                max_length=12,
                verbose_name="Customer Response",
            ),
        ),
    ]
