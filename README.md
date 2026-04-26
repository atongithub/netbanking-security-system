# Nexus Net Banking

A secure, modular web banking application with comprehensive security monitoring, transaction management and admin controls.

## Tech Stack

- **Backend**: Flask (Python) with MySQL
- **Frontend**: Vanilla JavaScript, Tailwind CSS
- **Database**: MySQL with 14 tables for banking operations
- **Architecture**: Modular Flask blueprints, RESTful API

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
# Configure database credentials in .env
python run.py
```

Server runs on `http://localhost:5000`

### Frontend

Open `public/index.html` in a browser or serve with:

```bash
python -m http.server 8000
```

Then navigate to `http://localhost:8000/public/`

## Features

- **User Authentication**: Login/logout with session tracking
- **Transaction Management**: Send money to beneficiaries with audit logs
- **Security Monitoring**: Failed login attempts, trusted device management, fraud alerts
- **Admin Dashboard**: User management, activity monitoring, system overview
- **Dark Mode**: Full UI support for light and dark themes
- **Audit Logging**: Complete activity history for compliance

## Admin Credentials

| Role | Username | Password |
|------|----------|----------|
| admin | admin | admin123 |

## API Documentation

See `backend/README.md` for complete API endpoint documentation.

## Project Structure

```
.
├── public/              # Frontend (HTML, CSS, JS)
├── backend/             # Flask API
│   ├── app/
│   │   ├── routes/      # API blueprints
│   │   └── utils/       # Shared utilities
│   └── run.py           # Entry point
├── package.json         # Project metadata
└── README.md            # This file
```

## Database

MySQL database: `netbankinglogging`

14 tables: users, bank_accounts, transactions, beneficiaries, login_sessions, activity_logs, fraud_alerts, trusted_devices, security_question_bank, user_security_questions, device_registry, failed_login_attempts, notifications, logs

## Security

- SHA-256 password hashing
- Session tokens with secrets module
- Input validation on all endpoints
- CORS enabled for frontend integration
- IP address tracking for logins
- Activity audit trail

## Development

Both backend and frontend run independently. Backend provides REST API; frontend consumes it.

Frontend API base: `http://localhost:5000/api/`

## License

This project is licensed under the MIT License.
