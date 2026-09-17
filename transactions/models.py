from django.db import models

from .constants import TRANSACTION_TYPE_CHOICES
from accounts.models import UserBankAccount


class Transaction(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='transactions',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    balance_after_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    interest_period = models.DateField(null=True, blank=True)
    transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']
        constraints = [
            models.UniqueConstraint(
                fields=['account', 'interest_period'],
                condition=models.Q(
                    transaction_type=3,
                    interest_period__isnull=False,
                ),
                name='unique_interest_period_per_account',
            ),
        ]
