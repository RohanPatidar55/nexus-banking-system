"""
Chatbot AI Service — Brain of the Nexus Banking Assistant.

Uses Ollama (local LLM) if available, otherwise falls back to an
intelligent rule-based engine that queries real user banking data.
"""
import json
import logging
import re
from datetime import timedelta
from decimal import Decimal

import requests
from django.db.models import Sum, Count
from django.utils import timezone

from accounts.models import UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


# ─────────────────────────────────────────────
#  1. Banking Data Helpers
# ─────────────────────────────────────────────

def _get_account(user):
    """Safely fetch the user's bank account."""
    try:
        return user.account
    except UserBankAccount.DoesNotExist:
        return None


def _get_balance(user):
    account = _get_account(user)
    if account:
        return f"₹{account.balance:,.2f}"
    return None


def _get_account_info(user):
    account = _get_account(user)
    if not account:
        return None
    return {
        "account_no": account.account_no,
        "account_type": account.account_type.name,
        "balance": f"₹{account.balance:,.2f}",
        "gender": account.get_gender_display() if hasattr(account, 'get_gender_display') else account.gender,
        "birth_date": str(account.birth_date) if account.birth_date else "N/A",
        "interest_rate": f"{account.account_type.annual_interest_rate}%",
        "max_withdrawal": f"₹{account.account_type.maximum_withdrawal_amount:,.2f}",
    }


def _get_recent_transactions(user, limit=5):
    account = _get_account(user)
    if not account:
        return []
    txns = Transaction.objects.filter(account=account).order_by('-timestamp')[:limit]
    result = []
    type_map = {DEPOSIT: "Deposit", WITHDRAWAL: "Withdrawal", INTEREST: "Interest"}
    for t in txns:
        result.append({
            "type": type_map.get(t.transaction_type, "Unknown"),
            "amount": f"₹{t.amount:,.2f}",
            "balance_after": f"₹{t.balance_after_transaction:,.2f}",
            "date": t.timestamp.strftime("%d %b %Y, %I:%M %p"),
        })
    return result


def _get_transaction_summary(user, days=30):
    account = _get_account(user)
    if not account:
        return None
    since = timezone.now() - timedelta(days=days)
    txns = Transaction.objects.filter(account=account, timestamp__gte=since)

    deposits = txns.filter(transaction_type=DEPOSIT).aggregate(
        total=Sum('amount'), count=Count('id')
    )
    withdrawals = txns.filter(transaction_type=WITHDRAWAL).aggregate(
        total=Sum('amount'), count=Count('id')
    )
    return {
        "period": f"Last {days} days",
        "deposits_total": f"₹{deposits['total'] or 0:,.2f}",
        "deposits_count": deposits['count'],
        "withdrawals_total": f"₹{withdrawals['total'] or 0:,.2f}",
        "withdrawals_count": withdrawals['count'],
        "net_flow": f"₹{(deposits['total'] or 0) - (withdrawals['total'] or 0):,.2f}",
    }


# ─────────────────────────────────────────────
#  2. Intent Detection
# ─────────────────────────────────────────────

def _detect_intent(message):
    """Simple keyword-based intent detection."""
    msg = message.lower().strip()

    # Balance
    if any(kw in msg for kw in ['balance', 'how much', 'money do i have', 'my money', 'kitna paisa', 'amount']):
        return 'balance'

    # Recent transactions
    if any(kw in msg for kw in ['recent', 'last transaction', 'latest transaction', 'history',
                                  'show transaction', 'my transaction', 'transaction list']):
        return 'recent_transactions'

    # Transaction summary/analytics
    if any(kw in msg for kw in ['summary', 'total deposit', 'total withdraw', 'spending',
                                  'this month', 'analytics', 'overview', 'report']):
        return 'summary'

    # Account info
    if any(kw in msg for kw in ['account number', 'account no', 'account info', 'account detail',
                                  'my account', 'account type', 'interest rate']):
        return 'account_info'

    # How to deposit
    if any(kw in msg for kw in ['how to deposit', 'deposit money', 'make a deposit', 'add money']):
        return 'help_deposit'

    # How to withdraw
    if any(kw in msg for kw in ['how to withdraw', 'withdraw money', 'take money', 'withdrawal']):
        return 'help_withdraw'

    # Greetings
    if any(kw in msg for kw in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'sup', 'yo']):
        return 'greeting'

    # Thanks
    if any(kw in msg for kw in ['thank', 'thanks', 'thx', 'appreciate']):
        return 'thanks'

    # Help
    if any(kw in msg for kw in ['help', 'what can you', 'commands', 'options', 'menu']):
        return 'help'

    # Goodbye
    if any(kw in msg for kw in ['bye', 'goodbye', 'see you', 'cya', 'quit', 'exit']):
        return 'goodbye'

    return 'unknown'


# ─────────────────────────────────────────────
#  3. Rule-Based Response Engine
# ─────────────────────────────────────────────

def _build_rule_response(intent, user):
    """Generate a response based on detected intent + real banking data."""

    if intent == 'greeting':
        name = user.first_name or "there"
        return f"Hey {name}! 👋 I'm your Nexus Banking Assistant. How can I help you today?"

    if intent == 'balance':
        balance = _get_balance(user)
        if balance:
            return f"💰 Your current balance is **{balance}**."
        return "⚠️ You don't seem to have a bank account yet. Please register first."

    if intent == 'recent_transactions':
        txns = _get_recent_transactions(user, limit=5)
        if not txns:
            return "📭 No transactions found. Make your first deposit to get started!"
        lines = ["📋 **Your Last 5 Transactions:**\n"]
        for i, t in enumerate(txns, 1):
            emoji = "🟢" if t['type'] == "Deposit" else "🔴" if t['type'] == "Withdrawal" else "💫"
            lines.append(f"{emoji} **{t['type']}** — {t['amount']}  |  Balance: {t['balance_after']}  |  {t['date']}")
        return "\n".join(lines)

    if intent == 'summary':
        summary = _get_transaction_summary(user)
        if not summary:
            return "⚠️ No account found. Please register first."
        return (
            f"📊 **Transaction Summary ({summary['period']}):**\n\n"
            f"🟢 Deposits: {summary['deposits_total']} ({summary['deposits_count']} transactions)\n"
            f"🔴 Withdrawals: {summary['withdrawals_total']} ({summary['withdrawals_count']} transactions)\n"
            f"📈 Net Flow: {summary['net_flow']}"
        )

    if intent == 'account_info':
        info = _get_account_info(user)
        if not info:
            return "⚠️ No account found. Register to create your bank account."
        return (
            f"🏦 **Account Details:**\n\n"
            f"• Account No: **{info['account_no']}**\n"
            f"• Type: {info['account_type']}\n"
            f"• Balance: {info['balance']}\n"
            f"• Interest Rate: {info['interest_rate']} per year\n"
            f"• Max Withdrawal: {info['max_withdrawal']}"
        )

    if intent == 'help_deposit':
        return (
            "💵 **How to Deposit Money:**\n\n"
            "1. Click **\"Deposit\"** in the navigation bar\n"
            "2. Enter the amount you want to deposit\n"
            "3. Click **Submit**\n\n"
            "The minimum deposit amount is ₹10."
        )

    if intent == 'help_withdraw':
        account = _get_account(user)
        max_amt = f"₹{account.account_type.maximum_withdrawal_amount:,.2f}" if account else "varies"
        return (
            f"🏧 **How to Withdraw Money:**\n\n"
            f"1. Click **\"Withdraw\"** in the navigation bar\n"
            f"2. Enter the amount (min ₹10, max {max_amt})\n"
            f"3. Click **Submit**\n\n"
            f"Make sure you have enough balance!"
        )

    if intent == 'thanks':
        return "You're welcome! 😊 Let me know if you need anything else."

    if intent == 'goodbye':
        return "Goodbye! 👋 Have a great day. Your money is safe with Nexus! 🔒"

    if intent == 'help':
        return (
            "🤖 **I can help you with:**\n\n"
            "• 💰 **\"What's my balance?\"** — Check your current balance\n"
            "• 📋 **\"Show my transactions\"** — View recent transactions\n"
            "• 📊 **\"Transaction summary\"** — Monthly deposit/withdrawal totals\n"
            "• 🏦 **\"Account info\"** — View your account details\n"
            "• 💵 **\"How to deposit?\"** — Deposit instructions\n"
            "• 🏧 **\"How to withdraw?\"** — Withdrawal instructions\n\n"
            "Just type naturally — I understand you! ✨"
        )

    # Unknown intent
    return (
        "🤔 I'm not sure I understand that. Try asking me:\n\n"
        "• \"What's my balance?\"\n"
        "• \"Show my recent transactions\"\n"
        "• \"Account info\"\n"
        "• \"Help\"\n\n"
        "I'm getting smarter every day! 🚀"
    )


# ─────────────────────────────────────────────
#  4. Ollama Integration (optional local LLM)
# ─────────────────────────────────────────────

def _try_ollama(message, user):
    """
    Try to use a local Ollama LLM for more natural responses.
    Falls back to rule-based if Ollama is not available.
    """
    # Build context about the user
    account = _get_account(user)
    context_parts = [f"User: {user.first_name} {user.last_name}"]
    if account:
        context_parts.append(f"Balance: ₹{account.balance:,.2f}")
        context_parts.append(f"Account Type: {account.account_type.name}")
        context_parts.append(f"Account No: {account.account_no}")

        # Recent transactions
        txns = _get_recent_transactions(user, limit=3)
        if txns:
            txn_str = "; ".join([f"{t['type']}: {t['amount']} on {t['date']}" for t in txns])
            context_parts.append(f"Recent transactions: {txn_str}")

    context = "\n".join(context_parts)

    prompt = (
        f"You are a helpful banking assistant for Nexus Banking System. "
        f"Be concise and friendly. Use emojis occasionally. "
        f"Here is the user's banking data:\n{context}\n\n"
        f"User asks: {message}\n\n"
        f"Respond helpfully in 2-3 sentences max. If they ask about balance or transactions, "
        f"use the real data above. Never make up numbers."
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
    except (requests.ConnectionError, requests.Timeout):
        pass
    except Exception as e:
        logger.warning(f"Ollama error: {e}")

    return None  # Signal to fall back to rule-based


# ─────────────────────────────────────────────
#  5. Main Entry Point
# ─────────────────────────────────────────────

def get_chatbot_response(message, user):
    """
    Main function called by the view.

    Strategy:
    1. Try Ollama (local LLM) for natural conversation
    2. Fall back to rule-based engine with real data
    """
    if not message or not message.strip():
        return "Please type a message! I'm here to help. 😊"

    # Try Ollama first
    ollama_response = _try_ollama(message, user)
    if ollama_response:
        return ollama_response

    # Fall back to rule-based
    intent = _detect_intent(message)
    return _build_rule_response(intent, user)
