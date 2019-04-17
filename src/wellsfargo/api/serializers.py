from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.reverse import reverse
from ipware import get_client_ip
from oscar.core.loading import get_model
from ..connector import actions
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT,
    ENGLISH, FRENCH,
    APPLICATION_FORM_EXCLUDE_FIELDS,
    PREQUAL_TRANS_STATUS_CHOICES,
    PREQUAL_CUSTOMER_RESP_NONE,
)
from ..core import exceptions as core_exceptions
from ..models import (
    APICredentials,
    FinancingPlan,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
    AccountInquiryResult,
    PreQualificationRequest,
    PreQualificationResponse,
    PreQualificationSDKApplicationResult,
)
from . import exceptions as api_exceptions

Basket = get_model('basket', 'Basket')
BillingAddress = get_model('order', 'BillingAddress')
PaymentEventType = get_model('order', 'PaymentEventType')
PaymentEvent = get_model('order', 'PaymentEvent')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')
ShippingAddress = get_model('order', 'ShippingAddress')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')
Transaction = get_model('payment', 'Transaction')


class AppSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = USCreditApp
        fields = ('region', 'app_type')


class BaseCreditAppSerializer(serializers.ModelSerializer):
    def save(self):
        request = self.context['request']

        request_user = None
        if request.user and request.user.is_authenticated:
            request_user = request.user

        # Build application class and save record to DB to record the attempt
        Application = self.Meta.model
        app = Application(**self.validated_data)

        # Store the ip address of user sending the request
        app.ip_address, _ = get_client_ip(request)

        app.user = request_user
        app.submitting_user = request_user
        app.save()

        # Submit application to to Wells
        try:
            result = actions.submit_credit_application(app, current_user=request_user)
        except core_exceptions.CreditApplicationPending as e:
            pending = api_exceptions.CreditApplicationPending()
            pending.inquiry = e.inquiry
            raise pending
        except core_exceptions.CreditApplicationDenied:
            raise api_exceptions.CreditApplicationDenied()
        except DjangoValidationError as e:
            raise DRFValidationError({
                'non_field_errors': [e.message]
            })
        return result


class USCreditAppSerializer(BaseCreditAppSerializer):
    region = serializers.ChoiceField(default=US, choices=(
        (US, _('United States')),
    ))
    app_type = serializers.ChoiceField(default=INDIVIDUAL, choices=(
        (INDIVIDUAL, _('Individual')),
    ))
    language = serializers.ChoiceField(default=ENGLISH, choices=(
        (ENGLISH, _('English')),
    ))

    class Meta:
        model = USCreditApp
        exclude = APPLICATION_FORM_EXCLUDE_FIELDS


class USJointCreditAppSerializer(BaseCreditAppSerializer):
    region = serializers.ChoiceField(default=US, choices=(
        (US, _('United States')),
    ))
    app_type = serializers.ChoiceField(default=JOINT, choices=(
        (JOINT, _('Joint')),
    ))
    language = serializers.ChoiceField(default=ENGLISH, choices=(
        (ENGLISH, _('English')),
    ))

    class Meta:
        model = USJointCreditApp
        exclude = APPLICATION_FORM_EXCLUDE_FIELDS


class CACreditAppSerializer(BaseCreditAppSerializer):
    region = serializers.ChoiceField(default=CA, choices=(
        (CA, _('Canada')),
    ))
    app_type = serializers.ChoiceField(default=INDIVIDUAL, choices=(
        (INDIVIDUAL, _('Individual')),
    ))
    language = serializers.ChoiceField(default=ENGLISH, choices=(
        (ENGLISH, _('English')),
        (FRENCH, _('French')),
    ))

    class Meta:
        model = CACreditApp
        exclude = APPLICATION_FORM_EXCLUDE_FIELDS


class CAJointCreditAppSerializer(BaseCreditAppSerializer):
    region = serializers.ChoiceField(default=CA, choices=(
        (CA, _('Canada')),
    ))
    app_type = serializers.ChoiceField(default=JOINT, choices=(
        (JOINT, _('Joint')),
    ))
    language = serializers.ChoiceField(default=ENGLISH, choices=(
        (ENGLISH, _('English')),
        (FRENCH, _('French')),
    ))

    class Meta:
        model = CAJointCreditApp
        exclude = APPLICATION_FORM_EXCLUDE_FIELDS


class FinancingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancingPlan
        fields = (
            'id',
            'plan_number',
            'description',
            'fine_print_superscript',
            'apr',
            'term_months',
            'allow_credit_application',
            'product_price_threshold',
        )


class EstimatedPaymentSerializer(serializers.Serializer):
    plan = FinancingPlanSerializer()
    principal = serializers.DecimalField(decimal_places=2, max_digits=12)
    monthly_payment = serializers.DecimalField(decimal_places=2, max_digits=12)
    loan_cost = serializers.DecimalField(decimal_places=2, max_digits=12)


class AccountInquirySerializer(serializers.ModelSerializer):
    account_number = serializers.RegexField('^[0-9]{16}$', max_length=16, min_length=16)

    class Meta:
        model = AccountInquiryResult
        read_only_fields = (
            'status',
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
        fields = read_only_fields + ('account_number', )


    def save(self):
        request = self.context['request']

        request_user = None
        if request.user and request.user.is_authenticated:
            request_user = request.user

        # Submit inquiry to Wells
        account_number = self.validated_data['account_number']
        try:
            result = actions.submit_inquiry(account_number, current_user=request_user)
        except DjangoValidationError as e:
            raise DRFValidationError({
                'account_number': [e.message]
            })

        return result


class PreQualificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreQualificationRequest
        read_only_fields = (
            'uuid',
            'credentials',
            'created_datetime',
            'modified_datetime',
        )
        fields = '__all__'


    def save(self):
        request = self.context['request']
        # Save IPAdress of the user
        user_ipaddress, _ = get_client_ip(request)
        self.validated_data['ip_address'] = user_ipaddress
        prequal_request = super().save()
        request_user = None
        if request.user and request.user.is_authenticated:
            request_user = request.user
        return_url = reverse('wfrs-api-prequal-app-complete', request=request)
        try:
            actions.check_pre_qualification_status(prequal_request, return_url=return_url, current_user=request_user)
        except DjangoValidationError as e:
            raise DRFValidationError({
                'non_field_errors': [e.message]
            })

        return prequal_request


class PreQualificationSDKApplicationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreQualificationSDKApplicationResult
        read_only_fields = (
            'created_datetime',
            'modified_datetime',
        )
        fields = read_only_fields + (
            'application_id',
            'first_name',
            'last_name',
            'application_status',
        )



class PreQualificationResponseSerializer(serializers.ModelSerializer):
    sdk_application_result = PreQualificationSDKApplicationResultSerializer(read_only=True)

    class Meta:
        model = PreQualificationResponse
        read_only_fields = (
            'status',
            'is_approved',
            'message',
            'credit_limit',
            'full_application_url',
            'sdk_application_result',
            'created_datetime',
            'modified_datetime',
        )
        fields = read_only_fields + ('customer_response', )


class PreQualificationSDKResponseSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=PREQUAL_TRANS_STATUS_CHOICES)
    credit_limit = serializers.DecimalField(decimal_places=2, max_digits=12, allow_null=True)
    response_id = serializers.CharField(max_length=8, allow_null=True)

    class Meta:
        model = PreQualificationRequest
        fields = (
            'customer_initiated',
            'email',
            'first_name',
            'middle_initial',
            'last_name',
            'line1',
            'line2',
            'city',
            'state',
            'postcode',
            'status',
            'credit_limit',
            'response_id',
        )


    def save(self):
        request = self.context['request']

        request_user = None
        if request.user and request.user.is_authenticated:
            request_user = request.user
        creds = APICredentials.get_credentials(request_user)
        request = PreQualificationRequest()
        request.customer_initiated = self.validated_data.get('customer_initiated', False)
        request.email = self.validated_data.get('email')
        request.first_name = self.validated_data['first_name']
        request.middle_initial = self.validated_data.get('middle_initial')
        request.last_name = self.validated_data['last_name']
        request.line1 = self.validated_data['line1']
        request.line2 = self.validated_data.get('line2')
        request.city = self.validated_data['city']
        request.state = self.validated_data['state']
        request.postcode = self.validated_data['postcode']
        request.credentials = creds
        request.ip_address, _ = get_client_ip(self.context['request'])
        request.save()

        if self.validated_data['response_id']:
            response = PreQualificationResponse()
            response.request = request
            response.status = self.validated_data['status']
            response.message = ''
            response.offer_indicator = ''
            response.credit_limit = self.validated_data['credit_limit']
            response.response_id = self.validated_data['response_id']
            response.application_url = ''
            response.customer_response = PREQUAL_CUSTOMER_RESP_NONE
            response.save()
        return request
