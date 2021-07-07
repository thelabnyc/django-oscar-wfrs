from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from ipware import get_client_ip
from oscar.core.loading import get_model
from ..connector import (
    PrequalAPIClient,
    CreditApplicationsAPIClient,
    AccountsAPIClient,
)
from ..core.constants import (
    PREQUAL_TRANS_STATUS_CHOICES,
    PREQUAL_CUSTOMER_RESP_NONE,
)
from ..core import exceptions as core_exceptions
from ..models import (
    CreditApplicationAddress,
    CreditApplicationApplicant,
    CreditApplication,
    FinancingPlan,
    AccountInquiryResult,
    PreQualificationRequest,
    PreQualificationResponse,
    PreQualificationSDKApplicationResult,
)
from . import exceptions as api_exceptions

Basket = get_model("basket", "Basket")
BillingAddress = get_model("order", "BillingAddress")
PaymentEventType = get_model("order", "PaymentEventType")
PaymentEvent = get_model("order", "PaymentEvent")
PaymentEventQuantity = get_model("order", "PaymentEventQuantity")
ShippingAddress = get_model("order", "ShippingAddress")
Source = get_model("payment", "Source")
SourceType = get_model("payment", "SourceType")
Transaction = get_model("payment", "Transaction")


class CreditApplicationAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditApplicationAddress
        fields = [
            "address_line_1",
            "address_line_2",
            "city",
            "state_code",
            "postal_code",
        ]
        extra_kwargs = {
            "address_line_2": {
                "required": False,
                "allow_null": True,
            },
        }


class CreditApplicationApplicantSerializer(serializers.ModelSerializer):
    address = CreditApplicationAddressSerializer()

    class Meta:
        model = CreditApplicationApplicant
        fields = [
            "first_name",
            "last_name",
            "middle_initial",
            "date_of_birth",
            "ssn",
            "annual_income",
            "email_address",
            "home_phone",
            "mobile_phone",
            "work_phone",
            "employer_name",
            "housing_status",
            "address",
        ]
        extra_kwargs = {
            "middle_initial": {
                "required": False,
                "allow_null": True,
            },
            "email_address": {
                "required": False,
                "allow_null": True,
            },
            "mobile_phone": {
                "required": False,
                "allow_null": True,
            },
            "work_phone": {
                "required": False,
                "allow_null": True,
            },
            "employer_name": {
                "required": False,
                "allow_null": True,
            },
            "housing_status": {
                "required": False,
                "allow_null": True,
            },
        }


class CreditApplicationSerializer(serializers.ModelSerializer):
    main_applicant = CreditApplicationApplicantSerializer()
    joint_applicant = CreditApplicationApplicantSerializer(
        required=False, allow_null=True
    )

    class Meta:
        model = CreditApplication
        fields = [
            "transaction_code",
            "reservation_number",
            "application_id",
            "requested_credit_limit",
            "language_preference",
            "salesperson",
            "main_applicant",
            "joint_applicant",
            "application_source",
        ]
        extra_kwargs = {
            "transaction_code": {
                "required": False,
            },
            "reservation_number": {
                "required": False,
                "allow_null": True,
            },
            "application_id": {
                "required": False,
                "allow_null": True,
            },
            "requested_credit_limit": {
                "required": False,
                "allow_null": True,
            },
            "language_preference": {
                "required": False,
            },
            "salesperson": {
                "required": False,
            },
            "application_source": {
                "required": False,
            },
        }

    def save(self):
        request = self.context["request"]
        request_user = None
        if request.user and request.user.is_authenticated:
            request_user = request.user

        # Build the main applicant object
        self.validated_data["main_applicant"][
            "address"
        ] = CreditApplicationAddress.objects.create(
            **self.validated_data["main_applicant"]["address"],
        )
        self.validated_data[
            "main_applicant"
        ] = CreditApplicationApplicant.objects.create(
            **self.validated_data["main_applicant"],
        )

        # Build the joint applicant object
        if self.validated_data.get("joint_applicant"):
            self.validated_data["joint_applicant"][
                "address"
            ] = CreditApplicationAddress.objects.create(
                **self.validated_data["joint_applicant"]["address"],
            )
            self.validated_data[
                "joint_applicant"
            ] = CreditApplicationApplicant.objects.create(
                **self.validated_data["joint_applicant"],
            )

        # Build the application object
        app = CreditApplication(**self.validated_data)

        # Store the ip address of user sending the request
        app.ip_address, _ = get_client_ip(request)
        app.user = request_user
        app.submitting_user = request_user
        app.save()

        # Submit application to to Wells
        client = CreditApplicationsAPIClient(current_user=request_user)
        try:
            result = client.submit_credit_application(app)
        except core_exceptions.CreditApplicationPending as e:
            pending = api_exceptions.CreditApplicationPending()
            pending.inquiry = e.inquiry
            raise pending
        except core_exceptions.CreditApplicationDenied:
            raise api_exceptions.CreditApplicationDenied()
        except DjangoValidationError as e:
            raise DRFValidationError(
                {
                    "non_field_errors": [str(m) for m in e.messages],
                }
            )
        return result


class FinancingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancingPlan
        fields = (
            "id",
            "plan_number",
            "description",
            "fine_print_superscript",
            "apr",
            "term_months",
            "allow_credit_application",
            "product_price_threshold",
        )


class EstimatedPaymentSerializer(serializers.Serializer):
    plan = FinancingPlanSerializer()
    principal = serializers.DecimalField(decimal_places=2, max_digits=12)
    monthly_payment = serializers.DecimalField(decimal_places=2, max_digits=12)
    loan_cost = serializers.DecimalField(decimal_places=2, max_digits=12)


class AccountInquirySerializer(serializers.ModelSerializer):
    account_number = serializers.RegexField("^[0-9]{16}$", max_length=16, min_length=16)
    main_applicant_address = CreditApplicationAddressSerializer(read_only=True)
    joint_applicant_address = CreditApplicationAddressSerializer(read_only=True)

    class Meta:
        model = AccountInquiryResult
        read_only_fields = (
            "main_applicant_full_name",
            "joint_applicant_full_name",
            "main_applicant_address",
            "joint_applicant_address",
            "credit_limit",
            "available_credit",
            "created_datetime",
            "modified_datetime",
        )
        fields = read_only_fields + ("account_number",)

    def save(self):
        request = self.context["request"]

        request_user = None
        if request.user and request.user.is_authenticated:
            request_user = request.user

        # Submit inquiry to Wells
        account_number = self.validated_data["account_number"]
        client = AccountsAPIClient(current_user=request_user)
        try:
            result = client.lookup_account_by_account_number(account_number)
        except DjangoValidationError as e:
            raise DRFValidationError(
                {
                    "account_number": [str(m) for m in e.messages],
                }
            )

        return result


class PreQualificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreQualificationRequest
        read_only_fields = (
            "uuid",
            "merchant_name",
            "merchant_num",
            "ip_address",
            "created_datetime",
            "modified_datetime",
        )
        fields = "__all__"

    def save(self):
        request = self.context["request"]
        # Save IPAdress of the user
        user_ipaddress, _ = get_client_ip(request)
        self.validated_data["ip_address"] = user_ipaddress
        prequal_request = super().save()
        request_user = None
        if request.user and request.user.is_authenticated:
            request_user = request.user
        client = PrequalAPIClient(current_user=request_user)
        try:
            client.check_prescreen_status(prequal_request)
        except DjangoValidationError as e:
            raise DRFValidationError(
                {
                    "non_field_errors": [str(m) for m in e.messages],
                }
            )
        return prequal_request


class PreQualificationSDKApplicationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreQualificationSDKApplicationResult
        read_only_fields = (
            "created_datetime",
            "modified_datetime",
        )
        fields = read_only_fields + (
            "application_id",
            "first_name",
            "last_name",
            "application_status",
        )


class PreQualificationRequestInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreQualificationRequest
        read_only_fields = (
            "uuid",
            "entry_point",
            "customer_initiated",
            "email",
            "first_name",
            "middle_initial",
            "last_name",
            "line1",
            "line2",
            "city",
            "state",
            "postcode",
        )
        fields = read_only_fields


class PreQualificationResponseSerializer(serializers.ModelSerializer):
    request = PreQualificationRequestInlineSerializer(read_only=True)
    sdk_application_result = PreQualificationSDKApplicationResultSerializer(
        read_only=True
    )

    class Meta:
        model = PreQualificationResponse
        read_only_fields = (
            "request",
            "status",
            "is_approved",
            "message",
            "offer_indicator",
            "credit_limit",
            "response_id",
            "full_application_url",
            "sdk_application_result",
            "created_datetime",
            "modified_datetime",
        )
        fields = read_only_fields + ("customer_response",)


class PreQualificationSDKResponseSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=PREQUAL_TRANS_STATUS_CHOICES)
    credit_limit = serializers.DecimalField(
        decimal_places=2, max_digits=12, allow_null=True
    )
    response_id = serializers.CharField(max_length=8, allow_null=True)

    class Meta:
        model = PreQualificationRequest
        fields = (
            "customer_initiated",
            "email",
            "first_name",
            "middle_initial",
            "last_name",
            "line1",
            "line2",
            "city",
            "state",
            "postcode",
            "merchant_name",
            "merchant_num",
            "status",
            "credit_limit",
            "response_id",
        )
        extra_kwargs = {
            "merchant_name": {
                "required": True,
                "allow_null": False,
            },
            "merchant_num": {
                "required": True,
                "allow_null": False,
            },
        }

    def save(self):
        request = PreQualificationRequest()
        request.customer_initiated = self.validated_data.get(
            "customer_initiated", False
        )
        request.email = self.validated_data.get("email")
        request.first_name = self.validated_data["first_name"]
        request.middle_initial = self.validated_data.get("middle_initial")
        request.last_name = self.validated_data["last_name"]
        request.line1 = self.validated_data["line1"]
        request.line2 = self.validated_data.get("line2")
        request.city = self.validated_data["city"]
        request.state = self.validated_data["state"]
        request.postcode = self.validated_data["postcode"]
        request.ip_address, _ = get_client_ip(self.context["request"])
        request.merchant_name = self.validated_data["merchant_name"]
        request.merchant_num = self.validated_data["merchant_num"]
        request.save()
        if self.validated_data["response_id"]:
            response = PreQualificationResponse()
            response.request = request
            response.status = self.validated_data["status"]
            response.message = ""
            response.offer_indicator = ""
            response.credit_limit = self.validated_data["credit_limit"]
            response.response_id = self.validated_data["response_id"]
            response.application_url = ""
            response.customer_response = PREQUAL_CUSTOMER_RESP_NONE
            response.save()
        return request
