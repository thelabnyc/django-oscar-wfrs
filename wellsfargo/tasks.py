from __future__ import absolute_import
from celery import shared_task
from django.core.exceptions import ValidationError
from wellsfargo.connector import actions
from wellsfargo.models import AccountMetadata
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def reconcile_accounts(self):
    for m in AccountMetadata.objects.order_by('account_id').all():
        account = m.account
        logger.info('Reconciling account %s' % account)
        try:
            resp = actions.submit_inquiry(account, current_user=account.primary_user)
            resp.reconcile()
        except ValidationError as e:
            logging.warning('Failed to reconcile account %s due to ValidationError[%s]' % (account, e.message))
