from django.core.management.base import BaseCommand
from wellsfargo import tasks


class Command(BaseCommand):
    help = "Fetch account status updates for all WFRS accounts"

    def handle(self, *args, **options):
        tasks.reconcile_accounts()
