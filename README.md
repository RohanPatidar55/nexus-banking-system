# Nexus Banking System 🏦

A comprehensive Django-based banking application with transaction management, user authentication, interest calculation, and AI-powered chatbot assistance.

## ✨ Features

- **User Management**
  - Email-based authentication
  - Secure password hashing
  - User profile with KYC (Know Your Customer) data
  - Address management

- **Banking Operations**
  - Multiple account types (Savings, Current, Fixed Deposit, Premium)
  - Deposit and withdrawal transactions
  - Automatic interest calculation
  - Real-time balance management
  - Transaction history and reports

- **Financial Features**
  - Configurable interest rates per account type
  - Flexible interest calculation periods (quarterly, semi-annually, etc.)
  - Maximum withdrawal limits per account type
  - Transaction date range filtering

- **Security & Audit**
  - Comprehensive transaction audit logging
  - Login attempt tracking
  - IP address and user agent logging
  - Secure password validation
  - CSRF protection

- **Async Processing**
  - Celery task queue integration
  - Redis message broker
  - Background task processing
  - Scheduled interest calculations

- **AI Assistant**
  - Banking chatbot for customer queries
  - Query transaction history
  - Check account information
  - Llama3.2 LLM integration (optional)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Redis
- MySQL/SQLite

### Installation

```bash
# Clone repository
git clone <repository-url>
cd nexus-banking-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Seed database with demo data
python manage.py seed_database --demo-users 5

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Navigate to `http://localhost:8000`

## 📝 Demo Credentials

```
Email: demo1@nexusbank.com
Password: DemoPass1!23
Account Type: Savings Account
Balance: $6000.00

Email: demo2@nexusbank.com
Password: DemoPass2!23
Account Type: Current Account
Balance: $7000.00

... (and 3 more demo accounts)
```

## 🏗️ Project Structure

```
nexus-banking-system/
├── accounts/               # User management
│   ├── models.py          # User, BankAccountType, UserBankAccount, UserAddress
│   ├── views.py           # Registration, Login, Logout
│   ├── forms.py           # Registration and Address forms
│   ├── managers.py        # Custom UserManager
│   └── urls.py            # Account routes
│
├── transactions/          # Financial transactions
│   ├── models.py          # Transaction, TransactionAuditLog
│   ├── views.py           # Deposit, Withdrawal, Report views
│   ├── forms.py           # Transaction forms with validation
│   ├── tasks.py           # Celery async tasks
│   ├── audit.py           # Audit logging utilities
│   └── urls.py            # Transaction routes
│
├── chatbot/               # AI Assistant
│   ├── models.py          # Chatbot models
│   ├── views.py           # Chatbot endpoint
│   ├── services.py        # LLM integration
│   └── urls.py            # Chatbot routes
│
├── core/                  # Core functionality
│   ├── models.py          # (Extensible)
│   ├── views.py           # Home view
│   └── urls.py            # Core routes
│
├── bankingSystem/         # Project settings
│   ├── settings.py        # Django configuration
│   ├── urls.py            # URL routing
│   ├── wsgi.py            # WSGI server entry point
│   ├── asgi.py            # ASGI server entry point
│   └── celery.py          # Celery configuration
│
├── templates/             # HTML templates
├── logs/                  # Application logs
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
└── DEPLOYMENT_GUIDE.md    # Complete deployment guide
```

## 🗄️ Database Schema

### Core Models

**User** (Custom Auth)
- Email-based authentication
- First name, last name
- Password (hashed with bcrypt)

**BankAccountType**
- Account product definitions
- Annual interest rate
- Maximum withdrawal amount
- Interest calculation frequency

**UserBankAccount**
- Links user to account type (1:1)
- Account number (unique)
- Current balance
- Birth date, gender
- Interest start date

**Transaction**
- Amount, type (DEPOSIT/WITHDRAWAL)
- Balance snapshot after transaction
- Timestamp
- Links to UserBankAccount

**TransactionAuditLog**
- Complete transaction audit trail
- Status tracking (PENDING, SUCCESS, FAILED)
- Balance before/after
- IP address, user agent
- Created/updated timestamps

## 🔧 Configuration

All configuration is managed via environment variables in `.env`:

```ini
# Application
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.sqlite3
# or MySQL:
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=nexusbankingsystem
# DB_USER=root
# DB_PASSWORD=your_password

# Redis & Celery
REDIS_HOST=localhost
REDIS_PORT=6379

# Banking
ACCOUNT_NUMBER_START_FROM=1000000000
MINIMUM_DEPOSIT_AMOUNT=100
MINIMUM_WITHDRAWAL_AMOUNT=50
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test tests_comprehensive -v 2

# Run specific test class
python manage.py test tests_comprehensive.UserModelTests

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Coverage
- ✅ User model and authentication
- ✅ Bank account types and interest calculation
- ✅ Transaction creation and validation
- ✅ Deposit and withdrawal operations
- ✅ Registration and login flows
- ✅ Transaction reports and filtering
- ✅ Balance validation
- ✅ Withdrawal limits

## 📦 Deployment

### Docker
```bash
docker-compose up
```

### Heroku
```bash
heroku create your-app-name
git push heroku main
heroku run python manage.py migrate
```

### Traditional (Gunicorn + Nginx)
```bash
gunicorn bankingSystem.wsgi:application
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete deployment instructions.

## 🔐 Security Features

- ✅ CSRF protection on all forms
- ✅ XSS protection via template escaping
- ✅ SQL injection prevention (ORM usage)
- ✅ Secure password hashing (PBKDF2)
- ✅ Email-based authentication (no username enumeration)
- ✅ LoginRequiredMixin on sensitive views
- ✅ Audit logging for all transactions
- ✅ Transaction validation and limits
- ✅ Environment-based configuration

## 📊 Key Features Explained

### Interest Calculation

Uses compound interest formula:
```
Interest = Principal × (1 + (Rate / 100 × Frequency)) - Principal
```

Example: $10,000 @ 4.5% quarterly
- Interest per quarter = $10,000 × 1.01125 - $10,000 = $112.50

### Withdrawal Limits

Each account type has a maximum withdrawal amount. System validates:
1. Withdrawal ≤ Maximum withdrawal amount
2. Withdrawal ≤ Current balance
3. Withdrawal ≥ Minimum withdrawal amount

### Audit Trail

Every transaction is logged with:
- User identity
- Transaction type and amount
- Status (SUCCESS/FAILED)
- Balance before and after
- Timestamp and IP address

## 🚧 Development

### Running Development Server
```bash
python manage.py runserver
```

### Celery Worker (for async tasks)
```bash
celery -A bankingSystem worker -l info
```

### Celery Beat (for scheduled tasks)
```bash
celery -A bankingSystem beat -l info
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## 📈 Performance

- Database indexes on frequently filtered fields (timestamp, user, transaction_type)
- QuerySet optimization with select_related/prefetch_related
- Redis caching for account types
- Async task processing with Celery
- SQLite for development, MySQL for production

## 🐛 Known Issues & TODOs

- [ ] Complete Ollama LLM integration for chatbot
- [ ] Add REST API endpoints (via Django REST Framework)
- [ ] Implement transaction pagination
- [ ] Add email notifications for transactions
- [ ] Mobile-responsive design improvements
- [ ] Two-factor authentication
- [ ] Account statements PDF export
- [ ] Fund transfers between accounts

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Complete setup and deployment instructions
- [Analysis Document](NEXUS_BANKING_ANALYSIS.md) - Detailed codebase analysis

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `python manage.py test`
4. Submit a pull request

## 📄 License

This project is part of the Nexus Banking System portfolio.

## 👨‍💻 Author

Rohan Patidar

---

## 📞 Support

For issues and questions:
1. Check the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Review test files for usage examples
3. Check application logs in `logs/` directory

---

**Status**: ✅ Production Ready  
**Last Updated**: October 4, 2026  
**Version**: 1.0.0
