from django.contrib import admin
from . import models


@admin.register(models.APICredentials)
class APICredentialsAdmin(admin.ModelAdmin):
    list_display = ['priority', 'username', 'merchant_num', 'user_group']


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


@admin.register(models.USCreditApp)
@admin.register(models.USJointCreditApp)
@admin.register(models.CACreditApp)
@admin.register(models.CAJointCreditApp)
class CreditAppAdmin(admin.ModelAdmin):
    list_display = ['email', 'region', 'language', 'app_type', 'user', 'created_datetime', 'modified_datetime']
    list_filter = ['created_datetime', 'modified_datetime']
