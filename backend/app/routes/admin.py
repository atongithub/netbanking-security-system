from flask import Blueprint, request, jsonify
from app.utils import get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard', methods=['GET'])
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

@admin_bp.route('/users', methods=['GET'])
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

@admin_bp.route('/users', methods=['POST'])
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

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
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

@admin_bp.route('/user/<int:user_id>/activity', methods=['GET'])
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
