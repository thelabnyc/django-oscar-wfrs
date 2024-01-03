# Generated by Django 2.2.8 on 2019-12-09 18:58

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0032_auto_20191209_1348"),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE wellsfargo_prequalificationrequest req
               SET merchant_num = creds.merchant_num,
                   merchant_name = creds.name
              FROM wellsfargo_apicredentials creds
             WHERE creds.id = req.credentials_id;
            """,
            """
            UPDATE wellsfargo_prequalificationrequest
               SET merchant_num = NULL,
                   merchant_name = NULL;
            """,
        ),
    ]
