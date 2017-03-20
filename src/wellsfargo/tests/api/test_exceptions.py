from django.test import TestCase
from rest_framework import status
from wellsfargo.api.exceptions import CreditApplicationPending, CreditApplicationDenied


class APIExceptionsTest(TestCase):
    def test_credit_app_pending(self):
        exc = CreditApplicationPending()
        self.assertEqual(exc.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(exc.get_codes(), 'pending')

    def test_credit_app_denied(self):
        exc = CreditApplicationDenied()
        self.assertEqual(exc.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(exc.get_codes(), 'denied')
