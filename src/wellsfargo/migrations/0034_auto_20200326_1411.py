# Generated by Django 2.2.11 on 2020-03-26 18:11

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import localflavor.us.models
import oscar.models.fields
import phonenumber_field.modelfields
import wellsfargo.core.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wellsfargo', '0033_auto_20191209_1358'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditApplicationAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_line_1', models.CharField(help_text='The street address line 1. This cannot contain a PO Box.', max_length=26, verbose_name='Address Line 1')),
                ('address_line_2', oscar.models.fields.NullCharField(help_text='The street address line 2.', max_length=26, verbose_name='Address Line 2')),
                ('city', models.CharField(help_text='The city component of the address.', max_length=18, verbose_name='City')),
                ('state_code', localflavor.us.models.USStateField(help_text='The two-letter US state code component of the address.', max_length=2, verbose_name='State')),
                ('postal_code', localflavor.us.models.USZipCodeField(help_text='US ZIP Code.', max_length=10, validators=[django.core.validators.MinLengthValidator(5), django.core.validators.MaxLengthValidator(5)], verbose_name='Postcode')),
            ],
        ),
        migrations.CreateModel(
            name='CreditApplicationApplicant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(help_text='The applicant’s first name.', max_length=15, verbose_name='First Name')),
                ('last_name', models.CharField(help_text='The applicant’s last name.', max_length=20, verbose_name='Last Name')),
                ('middle_initial', oscar.models.fields.NullCharField(help_text='The applicant’s middle initial.', max_length=1, verbose_name='Middle Initial')),
                ('date_of_birth', wellsfargo.core.fields.DateOfBirthField(help_text='The applicant’s date of birth.', null=True, verbose_name='Date of Birth')),
                ('ssn', wellsfargo.core.fields.USSocialSecurityNumberField(help_text='The applicant’s Social Security Number.', max_length=11, verbose_name='Social Security Number')),
                ('annual_income', models.IntegerField(help_text='The applicant’s annual income.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(999999)], verbose_name='Annual Income')),
                ('email_address', models.EmailField(blank=True, help_text='The applicant’s email address.', max_length=50, null=True, validators=[django.core.validators.MinLengthValidator(7)], verbose_name='Email')),
                ('home_phone', phonenumber_field.modelfields.PhoneNumberField(help_text='The applicant’s home phone number.', max_length=128, verbose_name='Home Phone')),
                ('mobile_phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='The applicant’s mobile phone number.', max_length=128, null=True, verbose_name='Mobile Phone')),
                ('work_phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='The applicant’s work phone number.', max_length=128, null=True, verbose_name='Work Phone')),
                ('employer_name', oscar.models.fields.NullCharField(help_text='The name of the applicant’s employer.', max_length=30, verbose_name='Employer Name')),
                ('housing_status', oscar.models.fields.NullCharField(choices=[('Rent', 'Rent'), ('Own', 'Own'), ('Other', 'Other')], help_text='The applicant’s housing status.', max_length=5, verbose_name='Housing Status')),
                ('address', models.ForeignKey(help_text='The applicant’s address.', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wellsfargo.CreditApplicationAddress', verbose_name='Address')),
            ],
        ),
        migrations.CreateModel(
            name='CreditApplication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_code', models.CharField(choices=[('A2', 'Applications from a non-consumer device'), ('AH', "Applications from a consumer's device"), ('A6', 'Credit application'), ('MAH', 'Merchant hosted at home, online'), ('MIS', 'Merchant hosted in store'), ('B1', 'Batch integrated at home'), ('B2', 'Batch get customer data'), ('B3', 'Batch merchant hosted in store'), ('B4', 'Batch merchant hosted at home')], default='MAH', help_text='Indicates where the transaction takes place.', max_length=3, verbose_name='Transaction Code')),
                ('reservation_number', oscar.models.fields.NullCharField(help_text='The unique code that correlates with the user’s reservation.', max_length=20, verbose_name='Reservation Number')),
                ('application_id', oscar.models.fields.NullCharField(help_text='An 8-character alphanumeric ID identifying the application.', max_length=8, verbose_name='Prequalified Application ID')),
                ('requested_credit_limit', models.IntegerField(blank=True, help_text='This denotes the total price value of the items that the applicant’s shopping cart.', null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99999)], verbose_name='Requested Credit Limit')),
                ('language_preference', models.CharField(choices=[('E', 'English'), ('S', 'Spanish')], default='E', help_text='The main applicant’s language preference values', max_length=1, verbose_name='Language Preference')),
                ('salesperson', oscar.models.fields.NullCharField(help_text='Alphanumeric value associated with the salesperson.', max_length=10, verbose_name='Sales Person ID')),
                ('main_applicant', models.ForeignKey(help_text='The main applicant’s personal details.', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wellsfargo.CreditApplicationApplicant', verbose_name='Main Applicant')),
                ('joint_applicant', models.ForeignKey(blank=True, help_text='The joint applicant’s details.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wellsfargo.CreditApplicationApplicant', verbose_name='Joint Applicant')),
                ('status', models.CharField(choices=[('', 'Unknown'), ('E0', 'Approved'), ('E1', 'Pending'), ('E2', 'Format Error'), ('E3', 'Wells Fargo Error'), ('E4', 'Denied')], default='', help_text='Application Status', max_length=2, verbose_name='Application Status')),
                ('application_source', models.CharField(default='Website', help_text='Where/how is user applying? E.g. Website, Call Center, In-Store, etc.', max_length=25, verbose_name='Application Source')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text="Submitting User's IP Address", null=True, verbose_name="Submitting User's IP Address")),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created Date/Time')),
                ('modified_datetime', models.DateTimeField(auto_now=True, verbose_name='Modified Date/Time')),
                ('credentials', models.ForeignKey(blank=True, help_text='Which merchant account submitted this application?', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wellsfargo.APICredentials', verbose_name='Merchant')),
            ],
            options={
                'verbose_name': 'Wells Fargo Credit Application',
                'verbose_name_plural': 'Wells Fargo Credit Applications',
            },
        ),
        migrations.AddField(
            model_name='accountinquiryresult',
            name='new_credit_app',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='wellsfargo.CreditApplication'),
        ),
        migrations.AddField(
            model_name='creditapplication',
            name='submitting_user',
            field=models.ForeignKey(blank=True, help_text='Select the user who filled out and submitted the credit application (not always the same as the user who is applying for credit).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Submitting User'),
        ),
        migrations.AddField(
            model_name='creditapplication',
            name='user',
            field=models.ForeignKey(blank=True, help_text='Select the user user who is applying and who will own (be the primary user of) this account.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Owner'),
        ),
        migrations.AddField(
            model_name='creditapplication',
            name='encrypted_account_number',
            field=models.BinaryField(null=True),
        ),
        migrations.AddField(
            model_name='creditapplication',
            name='last4_account_number',
            field=oscar.models.fields.NullCharField(max_length=4, verbose_name='Last 4 digits of account number'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='accountinquiryresult',
            name='joint_applicant_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wellsfargo.CreditApplicationAddress', verbose_name='Joint Applicant Address'),
        ),
        migrations.AddField(
            model_name='accountinquiryresult',
            name='joint_applicant_full_name',
            field=oscar.models.fields.NullCharField(max_length=50, verbose_name='Joint Applicant Name'),
        ),
        migrations.AddField(
            model_name='accountinquiryresult',
            name='main_applicant_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wellsfargo.CreditApplicationAddress', verbose_name='Main Applicant Address'),
        ),
        migrations.AddField(
            model_name='accountinquiryresult',
            name='main_applicant_full_name',
            field=oscar.models.fields.NullCharField(max_length=50, verbose_name='Main Applicant Name'),
        ),
    ]
