from django.test import TestCase
from django.urls import reverse

from .models import BankAccountType, User, UserAddress


class RegistrationTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Everyday',
            maximum_withdrawal_amount=1000,
            annual_interest_rate=6,
            interest_calculation_per_year=12,
        )

    def test_registration_creates_related_records_and_logs_in(self):
        response = self.client.post(
            reverse('accounts:user_registration'),
            {
                'first_name': 'Ada',
                'last_name': 'Lovelace',
                'email': 'ada@example.com',
                'password1': 'a-strong-password-123',
                'password2': 'a-strong-password-123',
                'account_type': self.account_type.pk,
                'gender': 'F',
                'birth_date': '1815-12-10',
                'street_address': '1 Analytical Engine Way',
                'city': 'London',
                'postal_code': 12345,
                'country': 'UK',
            },
        )

        self.assertRedirects(response, reverse('transactions:deposit_money'))
        user = User.objects.get(email='ada@example.com')
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertTrue(UserAddress.objects.filter(user=user).exists())
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(int(user.account.account_no), 1000000000 + user.pk)

    def test_login_authenticates_registered_user(self):
        user = User.objects.create_user(
            email='user@example.com',
            password='a-strong-password-123',
        )
        response = self.client.post(
            reverse('accounts:user_login'),
            {'username': user.email, 'password': 'a-strong-password-123'},
        )
        self.assertRedirects(response, reverse('home'))
