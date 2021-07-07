from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig


class WFRSConfig(OscarConfig):
    name = "wellsfargo"
    label = "wellsfargo"
    # Translators: Backend Library Name
    verbose_name = _("Wells Fargo Retail Services")
    namespace = "wellsfargo"

    def ready(self):
        from . import handlers  # NOQA
