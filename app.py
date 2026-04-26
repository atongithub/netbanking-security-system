import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'netbankinglogging'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Database error: {e}")
        return None

# Test database connection
try:
    conn = get_db_connection()
    if conn:
        print("✓ MySQL database connection successful")
        conn.close()
    else:
        print("✗ MySQL connection failed")
        exit(1)
except Exception as e:
    print(f"✗ MySQL connection failed: {e}")
    exit(1)

# Routes
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT user_id, username, first_name, email FROM users WHERE username = %s AND password_hash = %s",
            (username, password)
        )
        user = cursor.fetchone()
        
        if user:
            # Record login session with generated session_id
            try:
                cursor.execute("SELECT MAX(session_id) FROM login_sessions")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] else 0
                session_id = max_id + 1
                
                cursor.execute(
                    "INSERT INTO login_sessions (session_id, user_id, login_time, ip_address) VALUES (%s, %s, NOW(), %s)",
                    (session_id, user['user_id'], request.remote_addr or '0.0.0.0')
                )
                conn.commit()
            except Exception as log_error:
                print(f"Failed to log session: {log_error}")
            
            # Determine role based on user_id (99 = admin)
            role = 'admin' if user['user_id'] == 99 else 'user'
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'user': {
                    'id': user['user_id'],
                    'username': user['username'],
                    'name': user['first_name'],
                    'email': user['email']
                },
                'role': role
            }), 200
        else:
            # Record failed login attempt with generated attempt_id
            try:
                cursor.execute("SELECT MAX(attempt_id) FROM failed_login_attempts")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] else 0
                attempt_id = max_id + 1
                
                cursor.execute(
                    "SELECT user_id FROM users WHERE username = %s",
                    (username,)
                )
                user_record = cursor.fetchone()
                user_id = user_record['user_id'] if user_record else None
                
                cursor.execute(
                    "INSERT INTO failed_login_attempts (attempt_id, user_id, ip_address, attempt_time, failure_reason) VALUES (%s, %s, %s, NOW(), %s)",
                    (attempt_id, user_id, request.remote_addr or '0.0.0.0', 'Invalid credentials')
                )
                conn.commit()
            except Exception as log_error:
                print(f"Failed to log failed attempt: {log_error}")
            
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.email, u.is_active,
                   ba.account_number, ba.balance, ba.account_type, ba.status,
                   (SELECT MAX(login_time) FROM login_sessions WHERE user_id = u.user_id) as last_login,
                   (SELECT COUNT(*) FROM activity_logs WHERE user_id = u.user_id) as activity_count,
                   (SELECT COUNT(*) FROM transactions WHERE source_account = ba.account_number) as transactions_count
            FROM users u
            LEFT JOIN bank_accounts ba ON u.user_id = ba.user_id
            WHERE u.user_id != 99
            ORDER BY u.user_id
        """)
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users,
            'totalUsers': len(users)
        }), 200
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.email, 
                   ba.account_number, ba.balance, ba.account_type
            FROM users u
            LEFT JOIN bank_accounts ba ON u.user_id = ba.user_id
        """)
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'users': users}), 200
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/admin/users', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    phone = data.get('phone')
    account_type = data.get('accountType', 'Savings')
    initial_balance = data.get('initialBalance', 0)
    password = data.get('password')
    
    if not all([username, first_name, last_name, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get next user_id
        cursor.execute("SELECT MAX(user_id) as maxId FROM users")
        result = cursor.fetchone()
        next_user_id = (result[0] or 0) + 1
        
        # Insert user
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, email, phone_number, password_hash, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (next_user_id, username, first_name, last_name, email, phone or None, password, 1)
        )
        
        # Generate account number
        import random
        account_number = 1000 + random.randint(0, 9000)
        
        # Insert bank account
        cursor.execute(
            "INSERT INTO bank_accounts (account_number, user_id, account_type, balance, status) VALUES (%s, %s, %s, %s, %s)",
            (account_number, next_user_id, account_type, initial_balance, 'Active')
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'id': next_user_id,
            'username': username,
            'accountNumber': account_number
        }), 201
    except Exception as e:
        print(f"Create user error: {e}")
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/api/admin/user/<int:user_id>/activity', methods=['GET'])
def get_user_activity(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get activities through sessions
        cursor.execute("""
            SELECT al.log_id, al.action_type, al.target_entity, al.timestamp 
            FROM activity_logs al
            JOIN login_sessions ls ON al.session_id = ls.session_id
            WHERE ls.user_id = %s 
            ORDER BY al.timestamp DESC LIMIT 20
        """, (user_id,))
        activities = cursor.fetchall()
        
        # Get logins
        cursor.execute(
            "SELECT login_time, ip_address FROM login_sessions WHERE user_id = %s ORDER BY login_time DESC LIMIT 10",
            (user_id,)
        )
        logins = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'activities': activities,
            'logins': logins
        }), 200
    except Exception as e:
        print(f"User activity error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        affected = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected == 0:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
    except Exception as e:
        print(f"Delete user error: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500

@app.route('/api/user/<username>/overview', methods=['GET'])
def user_overview(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT user_id, first_name, username, email FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Log activity (get latest session for this user)
        try:
            cursor.execute(
                "SELECT session_id FROM login_sessions WHERE user_id = %s ORDER BY login_time DESC LIMIT 1",
                (user['user_id'],)
            )
            session = cursor.fetchone()
            if session:
                cursor.execute(
                    "SELECT MAX(log_id) FROM activity_logs"
                )
                result = cursor.fetchone()
                log_id = (result[0] if result and result[0] else 0) + 1
                
                cursor.execute(
                    "INSERT INTO activity_logs (log_id, session_id, action_type, target_entity, timestamp) VALUES (%s, %s, %s, %s, NOW())",
                    (log_id, session['session_id'], 'PROFILE_VIEW', f'User {username} viewed profile')
                )
                conn.commit()
        except Exception as log_error:
            print(f"Failed to log activity: {log_error}")
        
        cursor.execute(
            "SELECT account_number, balance, account_type, status FROM bank_accounts WHERE user_id = %s",
            (user['user_id'],)
        )
        account = cursor.fetchone()
        
        transactions = []
        if account:
            cursor.execute(
                "SELECT transaction_id, source_account, dest_account, amount, transaction_type, description, timestamp FROM transactions WHERE source_account = %s OR dest_account = %s ORDER BY timestamp DESC LIMIT 10",
                (account['account_number'], account['account_number'])
            )
            transactions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'profile': {
                'firstName': user['first_name'],
                'username': user['username'],
                'email': user['email']
            },
            'account': {
                'balance': float(account['balance']) if account else None,
                'accountNumber': account['account_number'] if account else None,
                'bankName': 'NetBanking',
                'status': account['status'] if account else None,
                'type': account['account_type'] if account else None
            } if account else None,
            'transactions': [
                {
                    'id': t['transaction_id'],
                    'sourceAccount': t['source_account'],
                    'destAccount': t['dest_account'],
                    'amount': float(t['amount']),
                    'type': t['transaction_type'],
                    'description': t['description'],
                    'timestamp': str(t['timestamp'])
                } for t in transactions
            ]
        }), 200
    except Exception as e:
        print(f"Overview error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    source_account = data.get('sourceAccount')
    dest_account = data.get('destAccount')
    amount = data.get('amount')
    description = data.get('description')
    
    if not all([source_account, dest_account, amount]) or amount <= 0:
        return jsonify({'error': 'Invalid transaction data'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check source account
        cursor.execute(
            "SELECT balance FROM bank_accounts WHERE account_number = %s",
            (source_account,)
        )
        source = cursor.fetchone()
        
        if not source or source[0] < amount:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Check destination account
        cursor.execute(
            "SELECT balance FROM bank_accounts WHERE account_number = %s",
            (dest_account,)
        )
        dest = cursor.fetchone()
        
        if not dest:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Destination account not found'}), 400
        
        # Transaction
        cursor.execute(
            "INSERT INTO transactions (source_account, dest_account, amount, transaction_type, description) VALUES (%s, %s, %s, %s, %s)",
            (source_account, dest_account, amount, 'Transfer', description or 'Transfer')
        )
        tx_id = cursor.lastrowid
        
        cursor.execute(
            "UPDATE bank_accounts SET balance = balance - %s WHERE account_number = %s",
            (amount, source_account)
        )
        
        cursor.execute(
            "UPDATE bank_accounts SET balance = balance + %s WHERE account_number = %s",
            (amount, dest_account)
        )
        
        # Log activity for source account user
        cursor.execute(
            "SELECT user_id FROM bank_accounts WHERE account_number = %s",
            (source_account,)
        )
        source_user = cursor.fetchone()
        if source_user:
            cursor.execute(
                "INSERT INTO activity_logs (user_id, activity_type, description, timestamp) VALUES (%s, %s, %s, NOW())",
                (source_user[0], 'TRANSFER_OUT', f'Transferred ₹{amount} to account {dest_account}')
            )
        
        # Log activity for destination account user
        cursor.execute(
            "SELECT user_id FROM bank_accounts WHERE account_number = %s",
            (dest_account,)
        )
        dest_user = cursor.fetchone()
        if dest_user:
            cursor.execute(
                "INSERT INTO activity_logs (user_id, activity_type, description, timestamp) VALUES (%s, %s, %s, NOW())",
                (dest_user[0], 'TRANSFER_IN', f'Received ₹{amount} from account {source_account}')
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'transactionId': tx_id}), 201
    except Exception as e:
        print(f"Transaction error: {e}")
        return jsonify({'error': 'Transaction failed'}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 50")
        transactions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(transactions), 200
    except Exception as e:
        print(f"Get transactions error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/admin/tables', methods=['GET'])
def get_tables():
    """Get list of all tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
        """, (db_config['database'],))
        
        tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'tables': tables}), 200
    except Exception as e:
        print(f"Get tables error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/admin/table/<table_name>', methods=['GET'])
def get_table_data(table_name):
    """Get all data from a specific table"""
    try:
        # Whitelist allowed tables to prevent SQL injection
        allowed_tables = [
            'users', 'bank_accounts', 'bank_details', 'login_sessions', 
            'activity_logs', 'transactions', 'beneficiaries', 'failed_login_attempts',
            'device_registry', 'trusted_devices', 'otp_validation', 
            'security_question_bank', 'user_security_questions', 
            'alert_severity_master', 'fraud_alerts'
        ]
        
        if table_name not in allowed_tables:
            return jsonify({'error': 'Invalid table'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1000")
        rows = cursor.fetchall()
        
        # Get column info
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'table': table_name,
            'columns': columns,
            'rows': rows,
            'count': len(rows)
        }), 200
    except Exception as e:
        print(f"Get table data error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/admin/table/<table_name>/<row_id>', methods=['PUT'])
def update_table_row(table_name, row_id):
    """Update a row in a table"""
    try:
        allowed_tables = [
            'users', 'bank_accounts', 'bank_details', 'login_sessions', 
            'activity_logs', 'transactions', 'beneficiaries', 'failed_login_attempts',
            'device_registry', 'trusted_devices', 'otp_validation', 
            'security_question_bank', 'user_security_questions', 
            'alert_severity_master', 'fraud_alerts'
        ]
        
        if table_name not in allowed_tables:
            return jsonify({'error': 'Invalid table'}), 400
        
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get primary key dynamically
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        pk_col = None
        for col in columns:
            if col[3] == 'PRI':  # KEY column
                pk_col = col[0]
                break
        
        if not pk_col:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No primary key found'}), 400
        
        # Build update query
        set_clause = ', '.join([f"{k}=%s" for k in data.keys()])
        values = list(data.values()) + [row_id]
        
        cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {pk_col}=%s", values)
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Row updated'}), 200
    except Exception as e:
        print(f"Update row error: {e}")
        return jsonify({'error': 'Update failed'}), 500

@app.route('/api/admin/table/<table_name>', methods=['POST'])
def insert_table_row(table_name):
    """Insert a new row into a table"""
    try:
        allowed_tables = [
            'users', 'bank_accounts', 'bank_details', 'login_sessions', 
            'activity_logs', 'transactions', 'beneficiaries', 'failed_login_attempts',
            'device_registry', 'trusted_devices', 'otp_validation', 
            'security_question_bank', 'user_security_questions', 
            'alert_severity_master', 'fraud_alerts'
        ]
        
        if table_name not in allowed_tables:
            return jsonify({'error': 'Invalid table'}), 400
        
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cols = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        cursor.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", values)
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'id': new_id}), 201
    except Exception as e:
        print(f"Insert row error: {e}")
        return jsonify({'error': 'Insert failed'}), 500

@app.route('/api/admin/table/<table_name>/<row_id>', methods=['DELETE'])
def delete_table_row(table_name, row_id):
    """Delete a row from a table"""
    try:
        allowed_tables = [
            'users', 'bank_accounts', 'bank_details', 'login_sessions', 
            'activity_logs', 'transactions', 'beneficiaries', 'failed_login_attempts',
            'device_registry', 'trusted_devices', 'otp_validation', 
            'security_question_bank', 'user_security_questions', 
            'alert_severity_master', 'fraud_alerts'
        ]
        
        if table_name not in allowed_tables:
            return jsonify({'error': 'Invalid table'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get primary key
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        pk_col = None
        for col in columns:
            if col[3] == 'PRI':
                pk_col = col[0]
                break
        
        if not pk_col:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No primary key found'}), 400
        
        cursor.execute(f"DELETE FROM {table_name} WHERE {pk_col}=%s", (row_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected == 0:
            return jsonify({'error': 'Row not found'}), 404
        return jsonify({'success': True, 'message': 'Row deleted'}), 200
    except Exception as e:
        print(f"Delete row error: {e}")
        return jsonify({'error': 'Delete failed'}), 500

if __name__ == '__main__':
    print(f"\n✓ NetBanking Server running on http://localhost:5000")
    print(f"✓ Database: {db_config['database']}")
    print(f"✓ Environment: development\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
