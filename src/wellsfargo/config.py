from django.apps import AppConfig


class Config(AppConfig):
    name = 'wellsfargo'
    label = 'wellsfargo'

    def ready(self):
        from . import handlers  # NOQA
