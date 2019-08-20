import django.dispatch


wfrs_app_approved = django.dispatch.Signal(providing_args=["app"])
