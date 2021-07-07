from django.core import signing, exceptions
from django.db import transaction
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework import views, generics, status, serializers
from oscarapi.basket import operations
from ..models import (
    APIMerchantNum,
    SDKMerchantNum,
    PreQualificationRequest,
    PreQualificationResponse,
    FinancingPlan,
    PreQualificationSDKApplicationResult,
    AccountInquiryResult,
)
from ..utils import list_plans_for_basket, calculate_monthly_payments
from .serializers import (
    CreditApplicationSerializer,
    FinancingPlanSerializer,
    EstimatedPaymentSerializer,
    AccountInquirySerializer,
    PreQualificationRequestSerializer,
    PreQualificationResponseSerializer,
    PreQualificationSDKResponseSerializer,
    PreQualificationSDKApplicationResultSerializer,
)
from .exceptions import CreditApplicationPending
import decimal

INQUIRY_SESSION_KEY = "wfrs-acct-inquiry-id"
PREQUAL_SESSION_KEY = "wfrs-prequal-request-id"
SDK_APP_RESULT_SESSION_KEY = "wfrs-sdk-app-result-id"


# This (non-atomic request) is needed because we use exceptions to bubble up the application pending / declined
# status, but when that happens we still want to save the application data (rather than rollback).
@method_decorator(transaction.non_atomic_requests, name="dispatch")
class CreditApplicationView(generics.GenericAPIView):
    serializer_class = CreditApplicationSerializer

    def post(self, request):
        request_ser = self.get_serializer_class()(
            data=request.data, context={"request": request}
        )
        request_ser.is_valid(raise_exception=True)
        try:
            result = request_ser.save()
        except CreditApplicationPending as e:
            request.session[INQUIRY_SESSION_KEY] = e.inquiry.pk
            raise e
        response_ser = AccountInquirySerializer(
            instance=result, context={"request": request}
        )
        request.session[INQUIRY_SESSION_KEY] = result.pk
        return Response(response_ser.data)


class FinancingPlanView(views.APIView):
    def get(self, request):
        basket = operations.get_basket(request)
        plans = list_plans_for_basket(basket)
        ser = FinancingPlanSerializer(plans, many=True)
        return Response(ser.data)


class EstimatedPaymentView(views.APIView):
    def get(self, request):
        # Validate the price input
        try:
            principal_price = request.GET.get("price", "")
            principal_price = decimal.Decimal(principal_price).quantize(
                decimal.Decimal("0.00")
            )
        except decimal.InvalidOperation:
            principal_price = decimal.Decimal("0.00")

        if not principal_price or principal_price <= 0:
            data = {
                "price": _("Submitted price parameter was not valid."),
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Get the best matching Financing Plan object for the price
        plan = FinancingPlan.get_advertisable_plan_by_price(principal_price)
        if not plan:
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Calculate the monthly payment
        monthly_payment = calculate_monthly_payments(
            principal_price, plan.term_months, plan.apr
        )

        # Calculate the total loan cost
        loan_cost = (monthly_payment * plan.term_months) - principal_price
        loan_cost = max(decimal.Decimal("0.00"), loan_cost)
        loan_cost = loan_cost.quantize(principal_price, rounding=decimal.ROUND_UP)

        # Return the payment data
        ser = EstimatedPaymentSerializer(
            instance={
                "plan": plan,
                "principal": principal_price,
                "monthly_payment": monthly_payment,
                "loan_cost": loan_cost,
            }
        )
        return Response(ser.data)


class UpdateAccountInquiryView(views.APIView):
    """
    After submitting a credit app, a client may use this view to update their credit limit info (for
    example, if the credit app was returned as pending).
    """

    def post(self, request):
        # Check for ID of last account inquiry in session (from the credit app view)
        inquiry_id = request.session.get(INQUIRY_SESSION_KEY)
        if not inquiry_id:
            return Response(status=status.HTTP_204_NO_CONTENT)
        try:
            inquiry = AccountInquiryResult.objects.get(pk=inquiry_id)
        except AccountInquiryResult.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        # Make sure we have an account number to work with
        account_number = inquiry.account_number
        if not account_number or account_number.startswith("xxxx"):
            return Response(status=status.HTTP_204_NO_CONTENT)
        # Perform another inquiry on the account
        request_ser = AccountInquirySerializer(
            data={"account_number": account_number}, context={"request": request}
        )
        request_ser.is_valid(raise_exception=True)
        result = request_ser.save()
        if result is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        # Update the inquiry source to match the original inquiry
        result.credit_app_source = inquiry.credit_app_source
        result.prequal_response_source = inquiry.prequal_response_source
        result.save()
        # Update the session to have the new inquiry ID
        request.session[INQUIRY_SESSION_KEY] = result.pk
        # Return the results
        response_ser = AccountInquirySerializer(
            instance=result, context={"request": request}
        )
        return Response(response_ser.data)


class SubmitAccountInquiryView(generics.GenericAPIView):
    serializer_class = AccountInquirySerializer

    def post(self, request):
        # Perform an account inquiry using the submitted account number
        request_ser = self.get_serializer_class()(
            data=request.data, context={"request": request}
        )
        request_ser.is_valid(raise_exception=True)
        result = request_ser.save()
        if result is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        # Update the session to have the new inquiry ID
        request.session[INQUIRY_SESSION_KEY] = result.pk
        # Return the results
        response_ser = self.get_serializer_class()(
            instance=result, context={"request": request}
        )
        return Response(response_ser.data)


class PreQualificationSDKMerchantNumView(generics.GenericAPIView):
    def get(self, request):
        # If this merchant number is used for following up on a prescreen offer, we have to use the API
        # merchant num, not the SDK merchant num.
        if request.GET.get("role") == "prescreen":
            creds = APIMerchantNum.get_for_user(request.user)
        else:
            creds = SDKMerchantNum.get_for_user(request.user)
        return Response(
            {
                "merchant_name": creds.name,
                "merchant_num": creds.merchant_num,
            }
        )


class PreQualificationResumeView(generics.GenericAPIView):
    def get(self, request, signed_prequal_request_id):
        # Validate signed ID
        signer = signing.Signer()
        try:
            prequal_request_id = signer.unsign(signed_prequal_request_id)
        except signing.BadSignature:
            raise exceptions.SuspiciousOperation("Invalid Signature")

        # Get and validate redirect URL
        redirect_url = self.request.GET.get("next", "/")
        redirect_url_is_safe = is_safe_url(
            url=redirect_url,
            allowed_hosts=set((request.get_host(),)),
            require_https=request.is_secure(),
        )
        if not redirect_url_is_safe:
            redirect_url = "/"

        # Make sure request ID is valid
        try:
            prequal_request = PreQualificationRequest.objects.get(pk=prequal_request_id)
        except PreQualificationRequest.DoesNotExist:
            raise exceptions.SuspiciousOperation(
                "PreQualificationRequest does not exist"
            )

        # Put ID into session and redirect to next view
        request.session[PREQUAL_SESSION_KEY] = prequal_request.pk
        return redirect(redirect_url)


class PreQualificationRequestView(generics.GenericAPIView):
    serializer_class = PreQualificationRequestSerializer

    def get(self, request):
        prequal_request_id = request.session.get(PREQUAL_SESSION_KEY)
        if not prequal_request_id:
            return Response(status=status.HTTP_204_NO_CONTENT)
        try:
            prequal_response = PreQualificationResponse.objects.get(
                request__id=prequal_request_id
            )
        except PreQualificationResponse.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        response_ser = PreQualificationResponseSerializer(
            instance=prequal_response, context={"request": request}
        )
        return Response(response_ser.data)

    def post(self, request):
        request_ser = self.get_serializer_class()(
            data=request.data, context={"request": request}
        )
        request_ser.is_valid(raise_exception=True)
        prequal_request = request_ser.save()
        try:
            prequal_response = prequal_request.response
        except PreQualificationResponse.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        request.session[PREQUAL_SESSION_KEY] = prequal_request.pk
        response_ser = PreQualificationResponseSerializer(
            instance=prequal_response, context={"request": request}
        )
        return Response(response_ser.data)


class PreQualificationSDKResponseView(PreQualificationRequestView):
    serializer_class = PreQualificationSDKResponseSerializer


class PreQualificationSDKApplicationResultView(generics.GenericAPIView):
    serializer_class = PreQualificationSDKApplicationResultSerializer

    def get(self, request):
        # Try to find an existing SDK app result for this session
        sdk_application_result = self._get_sdk_app_result_from_session(request)
        if sdk_application_result is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        response_ser = self.get_serializer_class()(
            instance=sdk_application_result, context={"request": request}
        )
        return Response(response_ser.data)

    def post(self, request):
        # Try to find an existing SDK app result for this session
        instance = self._get_sdk_app_result_from_session(request)
        # Save the SDK app response data
        request_ser = self.get_serializer_class()(
            instance=instance, data=request.data, context={"request": request}
        )
        request_ser.is_valid(raise_exception=True)
        sdk_application_result = request_ser.save()
        # Try to associate the SDK app result with the PreQual response data
        try:
            prequal_request_id = request.session.get(PREQUAL_SESSION_KEY)
            prequal_response = PreQualificationResponse.objects.get(
                request__id=prequal_request_id
            )
            sdk_application_result.prequal_response = prequal_response
            sdk_application_result.save()
        except PreQualificationResponse.DoesNotExist:
            pass
        # Update the ID in the session
        request.session[SDK_APP_RESULT_SESSION_KEY] = sdk_application_result.pk
        # Return the SDK app result data
        response_ser = self.get_serializer_class()(
            instance=sdk_application_result, context={"request": request}
        )
        return Response(response_ser.data)

    def _get_sdk_app_result_from_session(self, request):
        instance = None
        # Try looking up PreQualificationSDKApplicationResult by ID stored in the session
        sdk_app_result_id = request.session.get(SDK_APP_RESULT_SESSION_KEY)
        if sdk_app_result_id is not None:
            try:
                instance = PreQualificationSDKApplicationResult.objects.get(
                    pk=sdk_app_result_id
                )
            except PreQualificationSDKApplicationResult.DoesNotExist:
                pass
        # Try looking up PreQualificationSDKApplicationResult by session's PreQualificationRequest ID
        prequal_request_id = request.session.get(PREQUAL_SESSION_KEY)
        if prequal_request_id is not None:
            try:
                instance = PreQualificationSDKApplicationResult.objects.get(
                    prequal_response__request__id=prequal_request_id
                )
            except PreQualificationSDKApplicationResult.DoesNotExist:
                pass
        return instance


class PreQualificationCustomerResponseView(views.APIView):
    def post(self, request):
        prequal_request_id = request.session.get(PREQUAL_SESSION_KEY)
        if not prequal_request_id:
            raise serializers.ValidationError(
                _("No pre-qualification response was found for this session.")
            )
        try:
            prequal_response = PreQualificationResponse.objects.get(
                request__id=prequal_request_id
            )
        except PreQualificationResponse.DoesNotExist:
            raise serializers.ValidationError(
                _("No pre-qualification response was found for this session.")
            )
        serializer = PreQualificationResponseSerializer(
            instance=prequal_response, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
