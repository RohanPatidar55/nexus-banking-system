import json

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import BankAccountType, User, UserBankAccount


class ChatbotAuthorizationTests(TestCase):
    def setUp(self):
        account_type = BankAccountType.objects.create(
            name='Everyday',
            maximum_withdrawal_amount=1000,
            annual_interest_rate=6,
            interest_calculation_per_year=12,
        )
        self.user = User.objects.create_user(
            email='customer@example.com',
            password='a-strong-password-123',
        )
        UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1000000001,
            gender='F',
        )

    def test_unauthenticated_request_returns_json_401(self):
        response = self.client.post(
            reverse('chatbot:chat'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['reply'][0], '🔒')

    def test_authenticated_request_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(
            reverse('chatbot:chat'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
