from django.urls import reverse
from wellsfargo.models import USCreditApp
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests import responses
import mock


class ApplicationSelectionViewTest(BaseTest):
    def test_unauthorized(self):
        url = reverse('wfrs-apply-step1')
        resp = self.client.get(url)
        self.assertRedirects(resp, '/accounts/login/?next={}'.format(url))


    def test_get(self):
        self.client.login(username='bill', password='schmoe')
        url = reverse('wfrs-apply-step1')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)


    def test_post_valid(self):
        self.client.login(username='bill', password='schmoe')
        url = reverse('wfrs-apply-step1')

        resp = self.client.post(url, data={
            'region': 'US',
            'language': 'E',
            'app_type': 'I',
        })
        self.assertRedirects(resp, '/dashboard/wfrs/apply/US/E/I/')

        resp = self.client.post(url, data={
            'region': 'US',
            'language': 'E',
            'app_type': 'J',
        })
        self.assertRedirects(resp, '/dashboard/wfrs/apply/US/E/J/')


    def test_post_invalid(self):
        self.client.login(username='bill', password='schmoe')
        url = reverse('wfrs-apply-step1')
        resp = self.client.post(url, data={
            'region': 'MEX',
            'language': 'E',
            'app_type': 'I',
        })
        self.assertFormError(resp, 'form', 'region', [
            'Select a valid choice. MEX is not one of the available choices.'
        ])



class CreditApplicationViewTest(BaseTest):
    def build_valid_request(self):
        return {
            'region': 'US',
            'app_type': 'I',
            'language': 'E',
            'purchase_price': 2000,
            'main_ssn': '999999991',
            'main_first_name': 'Joe',
            'main_last_name': 'Schmoe',
            'main_date_of_birth': '1990-01-01',
            'email': 'foo@example.com',
            'main_address_line1': '123 Evergreen Terrace',
            'main_address_city': 'Springfield',
            'main_address_state': 'NY',
            'main_address_postcode': '10001',
            'main_annual_income': '100000',
            'main_home_phone': '+1 (212) 209-1333',
            'main_employer_phone': '+1 (212) 209-1333',
            'application_source': 'Unit Test',
        }

    def test_unauthorized(self):
        url = reverse('wfrs-apply-step2', args=('US', 'E', 'I'))
        resp = self.client.get(url)
        self.assertRedirects(resp, '/accounts/login/?next={}'.format(url))


    def test_get(self):
        self.client.login(username='bill', password='schmoe')
        url = reverse('wfrs-apply-step2', args=('US', 'E', 'I'))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)


    @mock.patch('soap.get_transport')
    def test_post_successful(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)
        self.client.login(username='bill', password='schmoe')
        url = reverse('wfrs-apply-step2', args=('US', 'E', 'I'))
        resp = self.client.post(url, data=self.build_valid_request())
        app = USCreditApp.objects.order_by('-pk').first()
        self.assertRedirects(resp, '/dashboard/wfrs/applications/us-individual/{}/'.format(app.pk))


    @mock.patch('soap.get_transport')
    def test_post_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_denied)
        self.client.login(username='bill', password='schmoe')
        url = reverse('wfrs-apply-step2', args=('US', 'E', 'I'))
        resp = self.client.post(url, data=self.build_valid_request())
        self.assertContains(resp, 'Credit Application was denied by Wells Fargo')


    @mock.patch('soap.get_transport')
    def test_post_pending(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_pending)
        self.client.login(username='bill', password='schmoe')
        url = reverse('wfrs-apply-step2', args=('US', 'E', 'I'))
        resp = self.client.post(url, data=self.build_valid_request(), follow=True)
        self.assertRedirects(resp, '/dashboard/wfrs/applications/')
        self.assertContains(resp, 'Credit Application approval is pending')
