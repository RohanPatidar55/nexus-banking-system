from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView

from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    WithdrawForm,
)
from accounts.models import UserBankAccount
from transactions.models import Transaction


class TransactionRepostView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    form_data = {}

    def get(self, request, *args, **kwargs):
        self.form_data = {}
        form = TransactionDateRangeForm(request.GET or None)
        if form.is_valid():
            self.form_data = form.cleaned_data

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )

        daterange = self.form_data.get("daterange")

        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account,
            'form': TransactionDateRangeForm(self.request.GET or None)
        })

        return context


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })

        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit Money to Your Account'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        with transaction.atomic():
            account = (
                UserBankAccount.objects
                .select_for_update()
                .select_related('account_type')
                .get(pk=self.request.user.account.pk)
            )
            if not account.initial_deposit_date:
                now = timezone.now()
                next_interest_month = int(
                    12 / account.account_type.interest_calculation_per_year
                )
                account.initial_deposit_date = now.date()
                account.interest_start_date = (
                    now + relativedelta(months=+next_interest_month)
                ).date()

            account.balance += amount
            account.save(update_fields=[
                'initial_deposit_date',
                'balance',
                'interest_start_date',
            ])
            form.instance.account = account
            form.instance.balance_after_transaction = account.balance
            form.instance.save()

        messages.success(
            self.request,
            f'{amount}$ was deposited to your account successfully'
        )

        self.object = form.instance
        return HttpResponseRedirect(self.get_success_url())


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money from Your Account'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        with transaction.atomic():
            account = (
                UserBankAccount.objects
                .select_for_update()
                .select_related('account_type')
                .get(pk=self.request.user.account.pk)
            )
            if amount > account.balance:
                form.add_error(
                    'amount',
                    f'You have {account.balance} $. You can not withdraw '
                    'more than your account balance',
                )
                return self.form_invalid(form)

            account.balance -= amount
            account.save(update_fields=['balance'])
            form.instance.account = account
            form.instance.balance_after_transaction = account.balance
            form.instance.save()

        messages.success(
            self.request,
            f'Successfully withdrawn {amount}$ from your account'
        )

        self.object = form.instance
        return HttpResponseRedirect(self.get_success_url())
