from django.apps import AppConfig


class Config(AppConfig):
    name = 'wellsfargo'
    label = 'wellsfargo'

    def ready(self):
        # Register signal handlers
        from . import handlers  # NOQA
