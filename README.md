# Django Financial Tracker

This is a Django web application that allows users to track their income, expenses, and investments. Users can also sign up using Google OAuth, receive notifications, and more.

## Features

1. **User Authentication**: Register, log in using **Google OAuth** or by email and password.
2. **Income and Expense Tracking**: Add, edit, and delete income and expense transactions.
3. **Dashboard**: A user-friendly dashboard to get an overview of financial status.
4. **Reporting**: Generate reports on financial data.
5. **Budgeting**: Set budget goals and track progress.
6. **Notification System**: Get email notifications about budget overruns.
8. **Expense Splitting**: Split expenses with others and track who owes whom.
9. **Receipt Uploading**: Upload and store receipts for transactions.

## Installation
### Clone the Repository

```bash
git clone https://github.com/yourusername/financial-tracker.git
cd financial-tracker
virtualenv .venv
.venv\Scripts\activate # for windows
source .venv\bin\activate # for linux
pip install -r requirements.txt
```

Now create a .env file and add the necessary variables, then run

```bash
python manage.py runserver
```

The app should be running at `127.0.0.1:8000`
