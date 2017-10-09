from django.contrib import admin
from . import models


class ReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + [field.name for field in obj._meta.fields] + [field.name for field in obj._meta.many_to_many]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.APICredentials)
class APICredentialsAdmin(admin.ModelAdmin):
    list_display = ['priority', 'username', 'merchant_num', 'user_group']


@admin.register(models.FinancingPlan)
class FinancingPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_number', 'description', 'apr', 'term_months']


@admin.register(models.FinancingPlanBenefit)
class FinancingPlanBenefitAdmin(admin.ModelAdmin):
    list_display = ['group_name']


@admin.register(models.TransferMetadata)
class TransferMetadataAdmin(ReadOnlyAdmin):
    list_display = ['auth_number', 'type_code', 'status', 'message']
    list_filter = ['type_code', 'status']


@admin.register(models.USCreditApp)
@admin.register(models.USJointCreditApp)
@admin.register(models.CACreditApp)
@admin.register(models.CAJointCreditApp)
class CreditAppAdmin(ReadOnlyAdmin):
    list_display = ['email', 'region', 'language', 'app_type', 'user', 'created_datetime', 'modified_datetime']
    list_filter = ['created_datetime', 'modified_datetime']


@admin.register(models.FraudScreenResult)
class FraudScreenResultAdmin(ReadOnlyAdmin):
    list_display = ['id', 'screen_type', 'order', 'decision', 'created_datetime']
    list_filter = ['screen_type', 'decision', 'created_datetime', 'modified_datetime']
    fields = (
        'screen_type',
        'order',
        'decision',
        'message',
        'created_datetime',
        'modified_datetime',
    )



@admin.register(models.AccountInquiryResult)
class AccountInquiryResultAdmin(ReadOnlyAdmin):
    list_display = ['masked_account_number', 'full_name', 'credit_limit', 'balance', 'open_to_buy', 'status', 'created_datetime']
    list_filter = ['status', 'created_datetime', 'modified_datetime']
    fields = (
        'status',
        'last4_account_number',
        'first_name',
        'middle_initial',
        'last_name',
        'phone_number',
        'address',
        'credit_limit',
        'balance',
        'open_to_buy',
        'last_payment_date',
        'last_payment_amount',
        'payment_due_date',
        'payment_due_amount',
        'created_datetime',
        'modified_datetime',
    )
