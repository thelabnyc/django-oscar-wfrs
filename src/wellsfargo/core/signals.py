import django.dispatch


# providing_args=["app"] is CreditApplication
wfrs_app_approved = django.dispatch.Signal()

# providing_args=["app"] is PreQualificationSDKApplicationResult
wfrs_sdk_app_approved = django.dispatch.Signal()
