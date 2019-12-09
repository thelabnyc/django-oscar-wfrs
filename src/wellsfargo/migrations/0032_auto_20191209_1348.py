# Generated by Django 2.2.8 on 2019-12-09 18:48

from django.db import migrations, models
import django.db.models.deletion
import oscar.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        ('wellsfargo', '0031_creditappindex'),
    ]

    operations = [
        migrations.AddField(
            model_name='prequalificationrequest',
            name='merchant_name',
            field=oscar.models.fields.NullCharField(max_length=200, verbose_name='Merchant Name'),
        ),
        migrations.AddField(
            model_name='prequalificationrequest',
            name='merchant_num',
            field=oscar.models.fields.NullCharField(max_length=200, verbose_name='Merchant Number'),
        ),
        migrations.AlterField(
            model_name='transfermetadata',
            name='type_code',
            field=models.CharField(choices=[('5', 'Authorization for Future Charge'), ('7', 'Cancel Existing Authorization'), ('2', 'Time-out Reversal for Previous "Authorization and Charge"'), ('4', 'Return or Credit'), ('9', 'Time-out Reversal for Return or Credit'), ('VS', 'Void Sale'), ('VR', 'Void Return')], max_length=2, verbose_name='Transaction Type'),
        ),
        migrations.CreateModel(
            name='SDKMerchantNum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.IntegerField(default=1, verbose_name='Priority Order')),
                ('name', models.CharField(default='Default', max_length=200, verbose_name='Name')),
                ('merchant_num', models.CharField(max_length=200, verbose_name='WFRS SDK Merchant Number')),
                ('user_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.Group')),
            ],
            options={
                'verbose_name': 'SDK Merchant Number',
                'verbose_name_plural': 'SDK Merchant Numbers',
                'ordering': ('-priority', '-id'),
            },
        ),
    ]
