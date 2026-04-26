# Banking API Backend

Modular Flask REST API for Nexus Net Banking with security monitoring, user/transaction management, and admin controls.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with DB credentials
python run.py
```

Runs on `http://localhost:5000`

## Architecture

Flask Blueprints pattern with separation:
- `routes/` - Auth, admin, CRUD, user, security endpoints
- `utils/` - Database, security, datetime utilities
- `app/__init__.py` - Factory function, blueprint registration

## API Endpoints

**Auth**: `POST /api/login`, `POST /api/logout`

**Admin**: `GET /api/admin/dashboard`, `GET/POST/DELETE /api/admin/users`, `GET /api/admin/user/<id>/activity`

**User**: `GET /api/user/<username>/overview`, `GET/POST /api/transactions`

**CRUD**: `GET /api/admin/tables`, `GET/POST /api/admin/table/<name>`, `PUT/DELETE /api/admin/table/<name>/<id>`

**Security**: Beneficiaries, fraud alerts, trusted devices, security questions, login sessions, activity logs, bank accounts, failed login attempts

All CRUD endpoints support 14 database tables with whitelist validation.

## Features

- SHA-256 password hashing
- Session tokens (secrets module)
- Input validation with regex patterns
- Activity audit trail
- Failed login tracking
- Multi-format datetime parsing (ISO, HTTP, MySQL)
- Dynamic primary key detection
- Whitelist-based CRUD (14 tables)

## Database Tables

users, bank_accounts, transactions, beneficiaries, login_sessions, failed_login_attempts, activity_logs, fraud_alerts, trusted_devices, device_registry, user_security_questions, security_question_bank, notifications, logs (14 total)

## Development

Add new routes by creating blueprint in `app/routes/`, import in `routes/__init__.py`, register in `app/__init__.py`.

```python
# app/routes/example.py
from flask import Blueprint

bp = Blueprint('example', __name__, url_prefix='/api')

@bp.route('/endpoint', methods=['GET'])
def handler():
    return {'success': True}
```

## Environment Variables

| Var | Default | Description |
|-----|---------|-------------|
| FLASK_ENV | development | dev/production |
| DB_HOST | localhost | MySQL host |
| DB_USER | root | DB user |
| DB_PASSWORD | root | DB password |
| DB_NAME | netbankinglogging | Database |
| DB_PORT | 3306 | MySQL port |

## Troubleshooting

- **DB Connection**: Check MySQL running, `.env` credentials, database exists
- **Import Errors**: `pip install -r requirements.txt`
- **Port in use**: Change port in `run.py`

## License

Proprietary - Nexus Net Banking
