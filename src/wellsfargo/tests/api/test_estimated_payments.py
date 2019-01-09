from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from wellsfargo.models import FinancingPlan


class EstimatedPaymentsTest(APITestCase):
    """"""
    def setUp(self):
        self.maxDiff = None
        self.plan1 = FinancingPlan.objects.create(
            plan_number=1001,
            description='Plan 1',
            apr='0.00',
            term_months=12,
            product_price_threshold='1000.00',
            advertising_enabled=True)
        self.plan2 = FinancingPlan.objects.create(
            plan_number=1002,
            description='Plan 2',
            apr='10.00',
            term_months=24,
            product_price_threshold='2000.00',
            advertising_enabled=True)


    def test_estimate_payments_no_price(self):
        url = reverse('wfrs-api-estimated-payment')
        resp = self.client.get('{}'.format(url))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


    def test_estimate_payments_invalid_price(self):
        url = reverse('wfrs-api-estimated-payment')
        resp = self.client.get('{}?price=foo'.format(url))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


    def test_estimate_below_min_threshold(self):
        url = reverse('wfrs-api-estimated-payment')
        resp = self.client.get('{}?price=500.00'.format(url))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


    def test_estimate_between_thresholds(self):
        url = reverse('wfrs-api-estimated-payment')
        resp = self.client.get('{}?price=1500.00'.format(url))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp.data['plan'] = dict(resp.data['plan'])
        self.assertDictEqual(resp.data, {
            "plan": {
                "id": self.plan1.pk,
                "plan_number": 1001,
                "description": "Plan 1",
                "fine_print_superscript": "",
                "apr": "0.00",
                "term_months": 12,
                "allow_credit_application": True,
                "product_price_threshold": '1000.00',
            },
            "principal": "1500.00",
            "monthly_payment": "125.00",
            "loan_cost": "0.00"
        })


    def test_estimate_above_thresholds(self):
        url = reverse('wfrs-api-estimated-payment')
        resp = self.client.get('{}?price=2500.00'.format(url))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp.data['plan'] = dict(resp.data['plan'])
        self.assertDictEqual(resp.data, {
            "plan": {
                "id": self.plan2.pk,
                "plan_number": 1002,
                "description": "Plan 2",
                "fine_print_superscript": "",
                "apr": "10.00",
                "term_months": 24,
                "allow_credit_application": True,
                "product_price_threshold": '2000.00',
            },
            "principal": "2500.00",
            "monthly_payment": "115.37",
            "loan_cost": "268.88"
        })
