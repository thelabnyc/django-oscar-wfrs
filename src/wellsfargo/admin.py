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


@admin.register(models.APIMerchantNum)
@admin.register(models.SDKMerchantNum)
class MerchantNumAdmin(admin.ModelAdmin):
    list_display = ['name', 'merchant_num', 'priority', 'user_group']


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


@admin.register(models.CreditApplication)
class CreditAppAdmin(ReadOnlyAdmin):
    list_filter = ['status', 'created_datetime', 'modified_datetime']


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
    list_display = ['masked_account_number', 'main_applicant_full_name', 'credit_limit', 'available_credit', 'created_datetime']
    list_filter = ['created_datetime', 'modified_datetime']
    fields = (
        'status',
        'last4_account_number',
        'main_applicant_full_name',
        'joint_applicant_full_name',
        'main_applicant_address',
        'joint_applicant_address',
        'credit_limit',
        'available_credit',
        'created_datetime',
        'modified_datetime',
    )
