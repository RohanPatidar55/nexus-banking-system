"""
Comprehensive test suite for Nexus Banking System
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import BankAccountType, UserBankAccount, UserAddress
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST

User = get_user_model()


class UserModelTests(TestCase):
    """Test User model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        """Test user creation with email"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_balance_property(self):
        """Test user balance property returns 0 when no account"""
        self.assertEqual(self.user.balance, 0)


class BankAccountTypeTests(TestCase):
    """Test BankAccountType model"""
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('4.5'),
            interest_calculation_per_year=4
        )
    
    def test_account_type_creation(self):
        """Test account type creation"""
        self.assertEqual(self.account_type.name, 'Savings')
        self.assertEqual(self.account_type.annual_interest_rate, Decimal('4.5'))
    
    def test_interest_calculation(self):
        """Test interest calculation formula"""
        principal = Decimal('10000.00')
        interest = self.account_type.calculate_interest(principal)
        
        # Interest = P * (1 + r/100n) - P
        # = 10000 * (1 + 4.5/(100*4)) - 10000
        # = 10000 * 1.01125 - 10000
        # = 112.50
        expected = Decimal('112.50')
        self.assertEqual(interest, expected)


class UserBankAccountTests(TestCase):
    """Test UserBankAccount model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='banker@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('4.5'),
            interest_calculation_per_year=4
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000001,
            gender='M',
            balance=Decimal('10000.00')
        )
    
    def test_account_creation(self):
        """Test account creation"""
        self.assertEqual(self.account.balance, Decimal('10000.00'))
        self.assertEqual(self.account.account_no, 1000001)
    
    def test_user_balance_with_account(self):
        """Test user balance property with account"""
        self.assertEqual(self.user.balance, Decimal('10000.00'))
    
    def test_interest_calculation_months(self):
        """Test interest calculation months"""
        from datetime import date
        self.account.interest_start_date = date(2024, 1, 1)
        self.account.save()
        
        months = self.account.get_interest_calculation_months()
        # With 4 times per year, interval is 12/4 = 3 months
        # Starting from January (month 1): [1, 4, 7, 10]
        self.assertEqual(months, [1, 4, 7, 10])


class TransactionModelTests(TestCase):
    """Test Transaction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='transact@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('4.5'),
            interest_calculation_per_year=4
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000001,
            gender='M',
            balance=Decimal('10000.00')
        )
    
    def test_deposit_transaction(self):
        """Test creating a deposit transaction"""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('1000.00'),
            balance_after_transaction=Decimal('11000.00'),
            transaction_type=DEPOSIT
        )
        
        self.assertEqual(transaction.amount, Decimal('1000.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)
        self.assertIsNotNone(transaction.timestamp)
    
    def test_withdrawal_transaction(self):
        """Test creating a withdrawal transaction"""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('500.00'),
            balance_after_transaction=Decimal('9500.00'),
            transaction_type=WITHDRAWAL
        )
        
        self.assertEqual(transaction.amount, Decimal('500.00'))
        self.assertEqual(transaction.transaction_type, WITHDRAWAL)


class RegistrationViewTests(TestCase):
    """Test user registration view"""
    
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('4.5'),
            interest_calculation_per_year=4
        )
    
    def test_registration_page_loads(self):
        """Test registration page loads"""
        response = self.client.get(reverse('accounts:user_registration'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01',
            'street_address': '123 Main St',
            'city': 'New York',
            'postal_code': 10001,
            'country': 'USA',
        }
        
        response = self.client.post(reverse('accounts:user_registration'), data)
        
        # Check user was created
        self.assertTrue(User.objects.filter(email='john@example.com').exists())
        user = User.objects.get(email='john@example.com')
        
        # Check account was created
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.account_type, self.account_type)


class DepositViewTests(TestCase):
    """Test deposit transaction view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='depositor@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('4.5'),
            interest_calculation_per_year=4
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000001,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_deposit_view_requires_login(self):
        """Test deposit view requires authentication"""
        response = self.client.get(reverse('transactions:deposit_money'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_deposit_transaction_success(self):
        """Test successful deposit"""
        self.client.login(username='depositor@example.com', password='testpass123')
        
        data = {
            'amount': '500.00',
            'transaction_type': DEPOSIT,
        }
        
        response = self.client.post(reverse('transactions:deposit_money'), data)
        
        # Refresh account
        self.account.refresh_from_db()
        
        # Check balance was updated
        self.assertEqual(self.account.balance, Decimal('1500.00'))
        
        # Check transaction was created
        transaction = Transaction.objects.filter(account=self.account).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('500.00'))


class WithdrawalViewTests(TestCase):
    """Test withdrawal transaction view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='withdrawer@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('4.5'),
            interest_calculation_per_year=4
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000001,
            gender='M',
            balance=Decimal('5000.00')
        )
    
    def test_withdrawal_exceeds_balance(self):
        """Test withdrawal exceeding balance fails"""
        self.client.login(username='withdrawer@example.com', password='testpass123')
        
        data = {
            'amount': '6000.00',
            'transaction_type': WITHDRAWAL,
        }
        
        response = self.client.post(reverse('transactions:withdraw_money'), data)
        
        # Check balance unchanged
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('5000.00'))
    
    def test_withdrawal_exceeds_limit(self):
        """Test withdrawal exceeding max withdrawal limit fails"""
        self.client.login(username='withdrawer@example.com', password='testpass123')
        
        data = {
            'amount': '6000.00',
            'transaction_type': WITHDRAWAL,
        }
        
        response = self.client.post(reverse('transactions:withdraw_money'), data)
        
        # Check balance unchanged
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('5000.00'))
    
    def test_withdrawal_success(self):
        """Test successful withdrawal"""
        self.client.login(username='withdrawer@example.com', password='testpass123')
        
        data = {
            'amount': '1000.00',
            'transaction_type': WITHDRAWAL,
        }
        
        response = self.client.post(reverse('transactions:withdraw_money'), data)
        
        # Check balance was updated
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('4000.00'))


class TransactionReportViewTests(TestCase):
    """Test transaction report view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='reporter@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('4.5'),
            interest_calculation_per_year=4
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000001,
            gender='M',
            balance=Decimal('10000.00')
        )
        
        # Create some transactions
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('1000.00'),
            balance_after_transaction=Decimal('11000.00'),
            transaction_type=DEPOSIT
        )
    
    def test_report_requires_login(self):
        """Test report view requires authentication"""
        response = self.client.get(reverse('transactions:transaction_report'))
        self.assertEqual(response.status_code, 302)
    
    def test_report_shows_transactions(self):
        """Test report shows user's transactions"""
        self.client.login(username='reporter@example.com', password='testpass123')
        
        response = self.client.get(reverse('transactions:transaction_report'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
