"""
Transaction audit logging model and utilities
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class TransactionAuditLog(models.Model):
    """Audit trail for all financial transactions"""
    
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
        ('INTEREST', 'Interest'),
        ('FAILED', 'Failed Transaction'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    balance_before = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} - {self.status}"
    
    @staticmethod
    def log_transaction(user, transaction_type, amount, status='SUCCESS', 
                       balance_before=None, balance_after=None, description='',
                       ip_address=None, user_agent=''):
        """
        Log a transaction to the audit trail
        
        Args:
            user: User instance
            transaction_type: Type of transaction
            amount: Transaction amount
            status: Status of transaction
            balance_before: Balance before transaction
            balance_after: Balance after transaction
            description: Additional description
            ip_address: IP address of user
            user_agent: User agent string
        """
        audit_log = TransactionAuditLog.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            status=status,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        logger.info(
            f"Transaction logged: {user.email} - {transaction_type} - "
            f"Amount: {amount} - Status: {status}"
        )
        
        return audit_log


class UserLoginAuditLog(models.Model):
    """Audit trail for user logins"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['-login_time']),
            models.Index(fields=['user', '-login_time']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.user.email} - Login {status} - {self.login_time}"
    
    @staticmethod
    def log_login(user, ip_address=None, user_agent='', success=True):
        """Log a user login"""
        log = UserLoginAuditLog.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )
        
        status_str = "successful" if success else "failed"
        logger.info(f"User {user.email} {status_str} login attempt from {ip_address}")
        
        return log
