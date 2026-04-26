from flask import Blueprint, request, jsonify
from app.utils import get_db_connection, validate_input, generate_session_token

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # Input validation
    if not validate_input(username, 'string', 50) or not password:
        return jsonify({'error': 'Invalid username or password'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # First, check if user exists
        cursor.execute(
            "SELECT user_id, username, first_name, email, is_active FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            # User doesn't exist - log failed attempt with NULL user_id
            try:
                cursor.execute("SELECT COALESCE(MAX(attempt_id), 0) as max_id FROM failed_login_attempts")
                result = cursor.fetchone()
                max_id = result['max_id'] if result else 0
                attempt_id = max_id + 1
                
                cursor.execute(
                    "INSERT INTO failed_login_attempts (attempt_id, user_id, ip_address, attempt_time, failure_reason) VALUES (%s, %s, %s, NOW(), %s)",
                    (attempt_id, None, request.remote_addr or '0.0.0.0', 'User not found')
                )
                conn.commit()
                print(f"Failed login recorded: attempt_id={attempt_id}, reason=User not found")
            except Exception as log_error:
                print(f"Failed to log failed attempt (user not found): {log_error}")
            
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # User exists - check password
        cursor.execute(
            "SELECT user_id, username, first_name, email, is_active FROM users WHERE username = %s AND password_hash = %s",
            (username, password)
        )
        user = cursor.fetchone()
        
        if not user:
            # Wrong password - log failed attempt
            try:
                cursor.execute("SELECT COALESCE(MAX(attempt_id), 0) as max_id FROM failed_login_attempts")
                result = cursor.fetchone()
                max_id = result['max_id'] if result else 0
                attempt_id = max_id + 1
                
                # Get user_id for this username
                cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                user_record = cursor.fetchone()
                user_id = user_record['user_id'] if user_record else None
                
                cursor.execute(
                    "INSERT INTO failed_login_attempts (attempt_id, user_id, ip_address, attempt_time, failure_reason) VALUES (%s, %s, %s, NOW(), %s)",
                    (attempt_id, user_id, request.remote_addr or '0.0.0.0', 'Wrong Password')
                )
                conn.commit()
                print(f"Failed login recorded: attempt_id={attempt_id}, user_id={user_id}, reason=Wrong Password")
            except Exception as log_error:
                print(f"Failed to log failed attempt (wrong password): {log_error}")
            
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is active
        if not user['is_active']:
            # Account inactive - log failed attempt
            try:
                cursor.execute("SELECT COALESCE(MAX(attempt_id), 0) as max_id FROM failed_login_attempts")
                result = cursor.fetchone()
                max_id = result['max_id'] if result else 0
                attempt_id = max_id + 1
                
                cursor.execute(
                    "INSERT INTO failed_login_attempts (attempt_id, user_id, ip_address, attempt_time, failure_reason) VALUES (%s, %s, %s, NOW(), %s)",
                    (attempt_id, user['user_id'], request.remote_addr or '0.0.0.0', 'Account Inactive')
                )
                conn.commit()
                print(f"Failed login recorded: attempt_id={attempt_id}, user_id={user['user_id']}, reason=Account Inactive")
            except Exception as log_error:
                print(f"Failed to log failed attempt (account inactive): {log_error}")
            
            cursor.close()
            conn.close()
            return jsonify({'error': 'Account inactive'}), 403
        
        # Credentials valid - Record successful login session
        session_id = None
        session_token = None
        try:
            cursor.execute("SELECT COALESCE(MAX(session_id), 0) as max_id FROM login_sessions")
            result = cursor.fetchone()
            max_id = result['max_id'] if result else 0
            session_id = max_id + 1
            
            # Generate session token
            session_token = generate_session_token()
            
            cursor.execute(
                "INSERT INTO login_sessions (session_id, user_id, login_time, ip_address, session_token) VALUES (%s, %s, NOW(), %s, %s)",
                (session_id, user['user_id'], request.remote_addr or '0.0.0.0', session_token)
            )
            conn.commit()
            print(f"Login session recorded: session_id={session_id}, user_id={user['user_id']}")
        except Exception as log_error:
            print(f"Failed to log login session: {log_error}")
        
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
            'role': role,
            'session_id': session_id,
            'session_token': session_token
        }), 200
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Authentication failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Record logout time for a session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'session_id required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE login_sessions SET logout_time = NOW() WHERE session_id = %s",
            (session_id,)
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected == 0:
            return jsonify({'error': 'Session not found'}), 404
        
        print(f"Logout recorded: session_id={session_id}")
        return jsonify({'success': True, 'message': 'Logout recorded'}), 200
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({'error': 'Failed to record logout'}), 500
