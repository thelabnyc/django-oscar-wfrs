from django.dispatch import receiver
from oscarapicheckout.signals import order_payment_authorized
from .api.views import PREQUAL_SESSION_KEY
from .models import PreQualificationResponse
import logging

logger = logging.getLogger(__name__)


@receiver(order_payment_authorized)
def link_prequal_request_to_order(sender, request, order, **kwargs):
    """When an order is placed, tie it to any pre-qualification data in the session that might exist"""
    prequal_request_id = request.session.get(PREQUAL_SESSION_KEY)
    if not prequal_request_id:
        return

    try:
        prequal_response = PreQualificationResponse.objects.get(
            request__id=prequal_request_id
        )
    except PreQualificationResponse:
        return

    # Link response to order
    logger.info(
        "Linking PreQualificationResponse[{}] to Order[{}]".format(
            prequal_response.pk, order.number
        )
    )
    prequal_response.customer_order = order
    prequal_response.save()

    # Wipe pre-qualification data out of the session
    request.session.get(PREQUAL_SESSION_KEY)
    del request.session[PREQUAL_SESSION_KEY]
    request.session.modified = True
