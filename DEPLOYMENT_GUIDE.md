# Nexus Banking System - Complete Setup & Deployment Guide

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Running the Application](#running-the-application)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [API Endpoints](#api-endpoints)
8. [Demo Credentials](#demo-credentials)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip and venv
- Redis (for Celery)
- MySQL/SQLite

### Installation

```bash
# Clone and navigate to project
cd nexus-banking-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_database --demo-users 5

# Create superuser for admin panel
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Navigate to `http://localhost:8000`

---

## 🔧 Environment Setup

### Configuration File (.env)

The project uses environment variables for configuration. Create a `.env` file in the project root:

```ini
# Django Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,.herokuapp.com

# Database (SQLite by default)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# For MySQL:
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=nexusbankingsystem
# DB_USER=root
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=3306

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Banking Settings
ACCOUNT_NUMBER_START_FROM=1000000000
MINIMUM_DEPOSIT_AMOUNT=100
MINIMUM_WITHDRAWAL_AMOUNT=50

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security (Production)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
```

### Security Notes for Production

```ini
DEBUG=False
SECRET_KEY=generate-a-secure-key-use-django-secret-key-generator
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

---

## 🗄️ Database Configuration

### SQLite (Default - Development)

```python
# .env
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

No additional setup needed. SQLite file will be created automatically.

### MySQL (Production Recommended)

1. **Install MySQL**
   ```bash
   # macOS
   brew install mysql

   # Ubuntu/Debian
   sudo apt-get install mysql-server

   # Windows
   # Download from https://dev.mysql.com/downloads/mysql/
   ```

2. **Create Database**
   ```sql
   CREATE DATABASE nexusbankingsystem;
   CREATE USER 'nexus'@'localhost' IDENTIFIED BY 'SecurePassword123!';
   GRANT ALL PRIVILEGES ON nexusbankingsystem.* TO 'nexus'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Configure .env**
   ```ini
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=nexusbankingsystem
   DB_USER=nexus
   DB_PASSWORD=SecurePassword123!
   DB_HOST=localhost
   DB_PORT=3306
   ```

4. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

### Redis Configuration

Redis is required for Celery task queue:

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# Windows
# Download from https://github.com/microsoftarchive/redis/releases
```

Verify Redis is running:
```bash
redis-cli ping
# Output: PONG
```

---

## ▶️ Running the Application

### Development Server

```bash
source venv/bin/activate
python manage.py runserver
```

Server runs on `http://localhost:8000`

### Celery Worker (For Async Tasks)

In a new terminal:

```bash
source venv/bin/activate
celery -A bankingSystem worker -l info
```

### Celery Beat (For Scheduled Tasks)

In another terminal:

```bash
source venv/bin/activate
celery -A bankingSystem beat -l info
```

### Admin Panel

Access Django admin at: `http://localhost:8000/admin/`

Default login credentials will be the superuser you created.

---

## 🧪 Testing

### Run All Tests

```bash
source venv/bin/activate
python manage.py test tests_comprehensive -v 2
```

### Run Specific Test Module

```bash
# Test user models
python manage.py test tests_comprehensive.UserModelTests

# Test transactions
python manage.py test tests_comprehensive.TransactionModelTests

# Test views
python manage.py test tests_comprehensive.DepositViewTests
```

### Test Coverage

```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report in htmlcov/
```

---

## 📦 Deployment

### Using Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       mysql-client \
       && rm -rf /var/lib/apt/lists/*

   # Copy requirements
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   # Copy project
   COPY . .

   # Collect static files
   RUN python manage.py collectstatic --noinput

   # Run migrations and start server
   CMD ["gunicorn", "bankingSystem.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```

2. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DEBUG=False
         - DB_ENGINE=django.db.backends.mysql
         - DB_NAME=nexus_banking
         - DB_USER=nexus
         - DB_PASSWORD=SecurePass123!
         - DB_HOST=db
       depends_on:
         - db
         - redis

     db:
       image: mysql:8.0
       environment:
         MYSQL_DATABASE: nexus_banking
         MYSQL_USER: nexus
         MYSQL_PASSWORD: SecurePass123!
         MYSQL_ROOT_PASSWORD: RootPass123!
       volumes:
         - mysql_data:/var/lib/mysql

     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"

     celery:
       build: .
       command: celery -A bankingSystem worker -l info
       depends_on:
         - db
         - redis
       environment:
         - DEBUG=False
         - DB_ENGINE=django.db.backends.mysql

   volumes:
     mysql_data:
   ```

3. **Run with Docker**
   ```bash
   docker-compose build
   docker-compose up
   ```

### Using Gunicorn + Nginx

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Create gunicorn_config.py**
   ```python
   bind = "0.0.0.0:8000"
   workers = 4
   worker_class = "sync"
   max_requests = 1000
   max_requests_jitter = 100
   timeout = 30
   keepalive = 5
   ```

3. **Run Gunicorn**
   ```bash
   gunicorn -c gunicorn_config.py bankingSystem.wsgi:application
   ```

4. **Nginx Configuration**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location /static/ {
           alias /path/to/staticfiles/;
       }

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Heroku Deployment

1. **Install Heroku CLI**
   ```bash
   brew tap heroku/brew && brew install heroku
   heroku login
   ```

2. **Create Procfile**
   ```
   web: gunicorn bankingSystem.wsgi:application
   worker: celery -A bankingSystem worker -l info
   beat: celery -A bankingSystem beat -l info
   ```

3. **Create runtime.txt**
   ```
   python-3.11.7
   ```

4. **Deploy**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   heroku create your-app-name
   heroku config:set DEBUG=False
   heroku config:set SECRET_KEY=your-secret-key
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

---

## 📡 API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/register/` - User registration
- `GET /accounts/logout/` - User logout

### Transactions
- `GET /transactions/report/` - View transaction history
- `POST /transactions/deposit/` - Deposit money
- `POST /transactions/withdraw/` - Withdraw money

### Admin
- `GET /admin/` - Django admin panel

### Chatbot
- `GET /chat/` - Chatbot interface
- `POST /chat/send/` - Send chatbot message

---

## 👥 Demo Credentials

After running `python manage.py seed_database`, use these credentials:

| Email | Password | Account Type |
|-------|----------|--------------|
| demo1@nexusbank.com | DemoPass1!23 | Savings Account |
| demo2@nexusbank.com | DemoPass2!23 | Current Account |
| demo3@nexusbank.com | DemoPass3!23 | Fixed Deposit |
| demo4@nexusbank.com | DemoPass4!23 | Premium Account |
| demo5@nexusbank.com | DemoPass5!23 | Savings Account |

---

## 🔐 Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS for your domain
- [ ] Use HTTPS/SSL certificates
- [ ] Set secure session and CSRF cookie flags
- [ ] Enable HSTS (HTTP Strict Transport Security)
- [ ] Configure strong database passwords
- [ ] Set up regular backups
- [ ] Enable audit logging for transactions
- [ ] Implement rate limiting on auth endpoints
- [ ] Use environment variables for all secrets
- [ ] Regular security updates

---

## 📊 Monitoring & Maintenance

### Check Application Status
```bash
# Test database connection
python manage.py dbshell

# Check migrations status
python manage.py showmigrations

# Test email configuration
python manage.py sendtestemail admin@example.com
```

### Logging

All logs are configured in `settings.py` and written to:
- `logs/banking.log` - General application logs
- `logs/transactions.log` - Financial transaction logs

View logs:
```bash
tail -f logs/banking.log
tail -f logs/transactions.log
```

### Database Backup

```bash
# SQLite backup
cp db.sqlite3 db.sqlite3.backup

# MySQL backup
mysqldump -u root -p nexusbankingsystem > backup.sql

# MySQL restore
mysql -u root -p nexusbankingsystem < backup.sql
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue: "No module named 'django'"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Issue: Database connection error**
```bash
# Verify database is running
# SQLite: db.sqlite3 should exist
# MySQL: mysql -u root -p

# Re-run migrations
python manage.py migrate
```

**Issue: Redis connection error**
```bash
# Start Redis
redis-server

# Verify Redis is running
redis-cli ping
```

**Issue: Static files not loading**
```bash
python manage.py collectstatic --noinput
```

---

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [MySQL Documentation](https://dev.mysql.com/doc/)

---

**Last Updated**: October 4, 2026
**Version**: 1.0
**Status**: ✅ Production Ready
