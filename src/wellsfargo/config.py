from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = 'wellsfargo'
    label = 'wellsfargo'
    # Translators: Backend Library Name
    verbose_name = _('Wells Fargo Retail Services')

    def ready(self):
        from . import handlers  # NOQA
