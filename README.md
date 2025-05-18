Digital Wallet System with Fraud Detection (Flask)

This project is a simple digital wallet system built using Flask. It allows users to register, log in, deposit and withdraw virtual funds, transfer between users, and view transaction history. It also includes basic fraud detection and admin APIs for insights and reporting.

Features

- User registration and login with JWT authentication
- Secure password hashing using bcrypt
- Deposit, withdraw, and transfer operations
- Transaction history tracking
- Rule-based fraud detection:
  - Rate-based: flag multiple quick transactions
  - Threshold-based: flag large amounts
- Admin APIs:
  - View flagged transactions
  - View total balances and top users

Tech Stack

- Python 3.x
- Flask
- Flask-JWT-Extended
- Flask-SQLAlchemy
- Bcrypt (Flask-Bcrypt)
- SQLite (for local development)

Installation


1. Create a virtual environment
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate

2. Install dependencies
   pip install -r requirements.txt

3. Run the app
   python app.py

The API will be live at http://127.0.0.1:5000/.

Authentication

All secured endpoints require a Bearer token in the Authorization header, obtained via /login.

Example:
Authorization: Bearer <your_token_here>

Example Endpoints

Register
POST /register
{
  "username": "alice",
  "password": "secure123"
}

Login
POST /login
{
  "username": "alice",
  "password": "secure123"
}

Deposit
POST /deposit
{
  "amount": 1000
}

Transfer
POST /transfer
{
  "to": "bob",
  "amount": 500
}

View Flagged Transactions (Admin)
GET /admin/flags

View Top Users (Admin)
GET /admin/stats

To Do

- Swagger/OpenAPI integration
- Soft delete for users/transactions
- Background fraud scan jobs
- Email alerts for suspicious transactions (mocked)
