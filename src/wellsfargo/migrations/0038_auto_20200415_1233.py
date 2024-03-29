# Generated by Django 2.2.12 on 2020-04-15 16:33

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import localflavor.us.models
import oscar.models.fields
import phonenumber_field.modelfields
import wellsfargo.core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("wellsfargo", "0037_auto_20200402_1108"),
    ]

    operations = [
        migrations.AlterField(
            model_name="creditapplication",
            name="transaction_code",
            field=models.CharField(
                choices=[
                    ("A2", "Applications from a non-consumer device"),
                    ("AH", "Applications from a consumer's device"),
                    ("A6", "Credit application"),
                    ("MAH", "Merchant hosted at home, online"),
                    ("MIS", "Merchant hosted in store"),
                    ("B1", "Batch integrated at home"),
                    ("B2", "Batch get customer data"),
                    ("B3", "Batch merchant hosted in store"),
                    ("B4", "Batch merchant hosted at home"),
                ],
                default="A6",
                help_text="Indicates where the transaction takes place.",
                max_length=3,
                verbose_name="Transaction Code",
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationaddress",
            name="address_line_1",
            field=models.CharField(max_length=26, verbose_name="Address Line 1"),
        ),
        migrations.AlterField(
            model_name="creditapplicationaddress",
            name="address_line_2",
            field=oscar.models.fields.NullCharField(
                max_length=26, verbose_name="Address Line 2"
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationaddress",
            name="city",
            field=models.CharField(max_length=18, verbose_name="City"),
        ),
        migrations.AlterField(
            model_name="creditapplicationaddress",
            name="postal_code",
            field=localflavor.us.models.USZipCodeField(
                max_length=10,
                validators=[
                    django.core.validators.MinLengthValidator(5),
                    django.core.validators.MaxLengthValidator(5),
                ],
                verbose_name="Postcode",
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationaddress",
            name="state_code",
            field=localflavor.us.models.USStateField(
                max_length=2, verbose_name="State"
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="address",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="wellsfargo.CreditApplicationAddress",
                verbose_name="Address",
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="annual_income",
            field=models.IntegerField(
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(999999),
                ],
                verbose_name="Annual Income",
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="date_of_birth",
            field=wellsfargo.core.fields.DateOfBirthField(
                null=True, verbose_name="Date of Birth"
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="email_address",
            field=models.EmailField(
                blank=True,
                max_length=50,
                null=True,
                validators=[django.core.validators.MinLengthValidator(7)],
                verbose_name="Email",
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="employer_name",
            field=oscar.models.fields.NullCharField(
                max_length=30, verbose_name="Employer Name"
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="first_name",
            field=models.CharField(max_length=15, verbose_name="First Name"),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="home_phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                max_length=128, verbose_name="Home Phone"
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="housing_status",
            field=oscar.models.fields.NullCharField(
                choices=[("Rent", "Rent"), ("Own", "Own"), ("Other", "Other")],
                max_length=5,
                verbose_name="Housing Status",
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="last_name",
            field=models.CharField(max_length=20, verbose_name="Last Name"),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="middle_initial",
            field=oscar.models.fields.NullCharField(
                max_length=1, verbose_name="Middle Initial"
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="mobile_phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=128, null=True, verbose_name="Mobile Phone"
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="ssn",
            field=wellsfargo.core.fields.USSocialSecurityNumberField(
                max_length=11, verbose_name="Social Security Number"
            ),
        ),
        migrations.AlterField(
            model_name="creditapplicationapplicant",
            name="work_phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=128, null=True, verbose_name="Work Phone"
            ),
        ),
    ]
