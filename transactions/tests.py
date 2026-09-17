from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import BankAccountType, User, UserBankAccount
from .constants import DEPOSIT, INTEREST, WITHDRAWAL
from .forms import TransactionDateRangeForm
from .models import Transaction
from .tasks import calculate_interest


class TransactionTests(TestCase):
    def setUp(self):
        account_type = BankAccountType.objects.create(
            name='Everyday',
            maximum_withdrawal_amount=1000,
            annual_interest_rate=12,
            interest_calculation_per_year=12,
        )
        self.user = User.objects.create_user(
            email='customer@example.com',
            password='a-strong-password-123',
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1000000001,
            gender='F',
        )
        self.client.login(
            username=self.user.email,
            password='a-strong-password-123',
        )

    def test_deposit_and_withdrawal_store_resulting_balances_atomically(self):
        self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': '100.00'},
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('100.00'))
        self.assertEqual(
            self.account.transactions.get().balance_after_transaction,
            Decimal('100.00'),
        )

        self.client.post(
            reverse('transactions:withdraw_money'),
            {'amount': '40.00'},
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('60.00'))
        self.assertEqual(
            self.account.transactions.order_by('-pk').first()
            .balance_after_transaction,
            Decimal('60.00'),
        )

    def test_interest_is_eligible_and_idempotent(self):
        today = timezone.localdate()
        self.account.balance = Decimal('100.00')
        self.account.initial_deposit_date = today
        self.account.interest_start_date = today
        self.account.save(update_fields=[
            'balance', 'initial_deposit_date', 'interest_start_date',
        ])

        calculate_interest()
        calculate_interest()

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('101.00'))
        interest_transactions = self.account.transactions.filter(
            transaction_type=INTEREST,
        )
        self.assertEqual(interest_transactions.count(), 1)
        self.assertEqual(
            interest_transactions.get().balance_after_transaction,
            Decimal('101.00'),
        )

    def test_date_range_validation_rejects_reverse_ranges(self):
        form = TransactionDateRangeForm({
            'daterange': '2026-09-20 - 2026-09-01',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('start date', form.errors['daterange'][0])

    def test_date_range_filters_transactions(self):
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('20.00'),
            balance_after_transaction=Decimal('20.00'),
            transaction_type=DEPOSIT,
        )
        response = self.client.get(
            reverse('transactions:transaction_report'),
            {'daterange': f'{date.today()} - {date.today()}'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['transaction_list']), 1)
