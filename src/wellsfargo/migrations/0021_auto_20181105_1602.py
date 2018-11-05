# Generated by Django 2.1.2 on 2018-11-05 21:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wellsfargo', '0020_prequalificationsdkapplicationresult'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prequalificationsdkapplicationresult',
            name='prequal_response',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sdk_application_result', to='wellsfargo.PreQualificationResponse', verbose_name='PreQualification Response'),
        ),
    ]
