from flask import Blueprint, request, jsonify
from app.utils import get_db_connection

user_bp = Blueprint('user', __name__, url_prefix='/api')

@user_bp.route('/user/<username>/overview', methods=['GET'])
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
            if session and session.get('session_id'):
                cursor.execute("SELECT COALESCE(MAX(log_id), 0) as max_id FROM activity_logs")
                max_id_result = cursor.fetchone()
                max_log_id = max_id_result['max_id'] if max_id_result else 0
                log_id = max_log_id + 1
                
                cursor.execute(
                    "INSERT INTO activity_logs (log_id, session_id, action_type, target_entity, timestamp) VALUES (%s, %s, %s, %s, NOW())",
                    (log_id, session['session_id'], 'PROFILE_VIEW', f'User {username} viewed profile')
                )
                conn.commit()
                print(f"Activity logged: log_id={log_id}, session_id={session['session_id']}")
        except Exception as log_error:
            print(f"Failed to log activity: {type(log_error).__name__}: {log_error}")
        
        cursor.execute(
            "SELECT account_number, balance, account_type, status FROM bank_accounts WHERE user_id = %s",
            (user['user_id'],)
        )
        account = cursor.fetchone()
        
        transactions = []
        if account:
            cursor.execute(
                "SELECT transaction_id, source_account, dest_account, amount, transaction_type, timestamp FROM transactions WHERE source_account = %s OR dest_account = %s ORDER BY timestamp DESC LIMIT 10",
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
                    'timestamp': str(t['timestamp'])
                } for t in transactions
            ]
        }), 200
    except Exception as e:
        print(f"Overview error: {e}")
        return jsonify({'error': 'Database error'}), 500

@user_bp.route('/transactions', methods=['POST'])
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

@user_bp.route('/transactions', methods=['GET'])
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
