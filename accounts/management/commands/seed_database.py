"""Django management command to seed the database with initial data"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from accounts.models import BankAccountType, UserBankAccount, UserAddress
from transactions.models import Transaction
from transactions.constants import DEPOSIT

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--demo-users',
            type=int,
            default=5,
            help='Number of demo users to create',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            User.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

        # Create bank account types
        self.stdout.write('\nCreating bank account types...')
        
        account_types_data = [
            {
                'name': 'Savings Account',
                'maximum_withdrawal_amount': Decimal('5000.00'),
                'annual_interest_rate': Decimal('4.5'),
                'interest_calculation_per_year': 4,
            },
            {
                'name': 'Current Account',
                'maximum_withdrawal_amount': Decimal('50000.00'),
                'annual_interest_rate': Decimal('0.0'),
                'interest_calculation_per_year': 1,
            },
            {
                'name': 'Fixed Deposit',
                'maximum_withdrawal_amount': Decimal('100000.00'),
                'annual_interest_rate': Decimal('6.5'),
                'interest_calculation_per_year': 1,
            },
            {
                'name': 'Premium Account',
                'maximum_withdrawal_amount': Decimal('10000.00'),
                'annual_interest_rate': Decimal('5.5'),
                'interest_calculation_per_year': 4,
            },
        ]
        
        for account_type_data in account_types_data:
            obj, created = BankAccountType.objects.get_or_create(
                name=account_type_data['name'],
                defaults=account_type_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {obj.name}'))
            else:
                self.stdout.write(f'  → Already exists: {obj.name}')
        
        # Create demo users
        num_demo_users = options['demo_users']
        self.stdout.write(f'\nCreating {num_demo_users} demo users...')
        
        account_types = list(BankAccountType.objects.all())
        
        for i in range(1, num_demo_users + 1):
            email = f'demo{i}@nexusbank.com'
            
            if User.objects.filter(email=email).exists():
                self.stdout.write(f'  → User {email} already exists')
                continue
            
            # Create user
            user = User.objects.create_user(
                email=email,
                password=f'DemoPass{i}!23',
                first_name=f'Demo',
                last_name=f'User{i}',
            )
            
            # Create address
            UserAddress.objects.create(
                user=user,
                street_address=f'{100 + i} Main Street',
                city='New York',
                postal_code=10001 + i,
                country='USA',
            )
            
            # Create bank account
            account_type = account_types[i % len(account_types)]
            account = UserBankAccount.objects.create(
                user=user,
                account_type=account_type,
                account_no=1000000 + (100 * i),
                gender='M' if i % 2 == 0 else 'F',
                balance=Decimal(f'{5000 + (i * 1000)}.00'),
            )
            
            # Create sample transactions
            Transaction.objects.create(
                account=account,
                amount=Decimal(f'{1000 + (i * 100)}.00'),
                balance_after_transaction=account.balance,
                transaction_type=DEPOSIT,
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Created user: {user.email} (Account: {account.account_no})'
            ))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database seeding completed successfully!'))
        
        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total Users: {User.objects.count()}')
        self.stdout.write(f'Total Account Types: {BankAccountType.objects.count()}')
        self.stdout.write(f'Total Bank Accounts: {UserBankAccount.objects.count()}')
        self.stdout.write(f'Total Transactions: {Transaction.objects.count()}')
        self.stdout.write('\nDemo Users (login credentials):')
        for i in range(1, min(num_demo_users + 1, 6)):
            email = f'demo{i}@nexusbank.com'
            password = f'DemoPass{i}!23'
            self.stdout.write(f'  • Email: {email}')
            self.stdout.write(f'    Password: {password}')
