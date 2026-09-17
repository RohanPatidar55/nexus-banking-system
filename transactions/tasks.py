from django.db import IntegrityError, transaction
from django.utils import timezone

from celery import shared_task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


@shared_task(name="calculate_interest")
def calculate_interest():
    today = timezone.localdate()
    interest_period = today.replace(day=1)
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=today,
        initial_deposit_date__isnull=False,
    ).select_related('account_type')

    for account in accounts:
        interval = 12 // account.account_type.interest_calculation_per_year
        months_since_start = (
            (today.year - account.interest_start_date.year) * 12
            + today.month - account.interest_start_date.month
        )
        if months_since_start >= 0 and months_since_start % interval == 0:
            with transaction.atomic():
                locked_account = (
                    UserBankAccount.objects.select_for_update()
                    .select_related('account_type')
                    .get(pk=account.pk)
                )
                if Transaction.objects.filter(
                    account=locked_account,
                    transaction_type=INTEREST,
                    interest_period=interest_period,
                ).exists():
                    continue

                interest = locked_account.account_type.calculate_interest(
                    locked_account.balance
                )
                locked_account.balance += interest
                locked_account.save(update_fields=['balance'])
                try:
                    Transaction.objects.create(
                        account=locked_account,
                        transaction_type=INTEREST,
                        amount=interest,
                        balance_after_transaction=locked_account.balance,
                        interest_period=interest_period,
                    )
                except IntegrityError:
                    # A concurrent worker already applied this period.
                    continue
