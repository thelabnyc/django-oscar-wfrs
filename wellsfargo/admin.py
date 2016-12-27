from django.contrib import admin
from . import models


@admin.register(models.APICredentials)
class APICredentialsAdmin(admin.ModelAdmin):
    list_display = ['priority', 'username', 'password', 'merchant_num', 'user_group']


@admin.register(models.AccountMetadata)
class AccountMetadataAdmin(admin.ModelAdmin):
    list_display = ['account', 'locale', 'account_number']
    list_filter = ['locale']


@admin.register(models.TransferMetadata)
class TransferMetadataAdmin(admin.ModelAdmin):
    list_display = ['auth_number', 'type_code', 'status', 'message']
    list_filter = ['type_code', 'status']


@admin.register(models.FinancingPlan)
class FinancingPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_number', 'description', 'apr', 'term_months']


@admin.register(models.FinancingPlanBenefit)
class FinancingPlanBenefitAdmin(admin.ModelAdmin):
    list_display = ['group_name']


@admin.register(models.TransactionRequest)
class TransactionRequestAdmin(admin.ModelAdmin):
    list_display = ['source_account', 'dest_account', 'ticket_number', 'created_datetime', 'modified_datetime']
    list_filter = ['type_code', 'financing_plan', 'created_datetime', 'modified_datetime']


@admin.register(models.USCreditApp)
@admin.register(models.USJointCreditApp)
@admin.register(models.CACreditApp)
@admin.register(models.CAJointCreditApp)
class CreditAppAdmin(admin.ModelAdmin):
    list_display = ['email', 'account', 'region', 'language', 'app_type', 'user', 'created_datetime', 'modified_datetime']
    list_filter = ['created_datetime', 'modified_datetime']
