from flask import Blueprint, request, jsonify
from app.utils import get_db_connection

security_bp = Blueprint('security', __name__, url_prefix='/api')

# ==================== BENEFICIARIES ====================
@security_bp.route('/beneficiaries', methods=['GET'])
def get_beneficiaries():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM beneficiaries WHERE user_id = %s ORDER BY beneficiary_id",
            (user_id,)
        )
        beneficiaries = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': beneficiaries}), 200
    except Exception as e:
        print(f"Get beneficiaries error: {e}")
        return jsonify({'error': 'Failed to fetch beneficiaries'}), 500

@security_bp.route('/beneficiaries', methods=['POST'])
def create_beneficiary():
    try:
        data = request.json
        required = ['user_id', 'account_number', 'nickname']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(beneficiary_id) FROM beneficiaries")
        max_id = cursor.fetchone()[0] or 0
        beneficiary_id = max_id + 1
        
        cursor.execute(
            "INSERT INTO beneficiaries (beneficiary_id, user_id, account_number, nickname, relationship_tag) VALUES (%s, %s, %s, %s, %s)",
            (beneficiary_id, data['user_id'], data['account_number'], data['nickname'], data.get('relationship_tag'))
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'beneficiary_id': beneficiary_id}), 201
    except Exception as e:
        print(f"Create beneficiary error: {e}")
        return jsonify({'error': 'Failed to create beneficiary'}), 500

@security_bp.route('/beneficiaries/<int:beneficiary_id>', methods=['PUT'])
def update_beneficiary(beneficiary_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        for field in ['nickname', 'relationship_tag', 'account_number']:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        
        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(beneficiary_id)
        query = f"UPDATE beneficiaries SET {', '.join(updates)} WHERE beneficiary_id = %s"
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Update beneficiary error: {e}")
        return jsonify({'error': 'Failed to update beneficiary'}), 500

@security_bp.route('/beneficiaries/<int:beneficiary_id>', methods=['DELETE'])
def delete_beneficiary(beneficiary_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM beneficiaries WHERE beneficiary_id = %s", (beneficiary_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Delete beneficiary error: {e}")
        return jsonify({'error': 'Failed to delete beneficiary'}), 500

# ==================== FRAUD ALERTS ====================
@security_bp.route('/fraud-alerts', methods=['GET'])
def get_fraud_alerts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT fa.*, u.username, t.amount FROM fraud_alerts fa LEFT JOIN users u ON fa.user_id = u.user_id LEFT JOIN transactions t ON fa.transaction_id = t.transaction_id ORDER BY fa.alert_id DESC"
        )
        alerts = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': alerts}), 200
    except Exception as e:
        print(f"Get fraud alerts error: {e}")
        return jsonify({'error': 'Failed to fetch alerts'}), 500

@security_bp.route('/fraud-alerts/<int:alert_id>', methods=['PUT'])
def update_fraud_alert(alert_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE fraud_alerts SET severity_level = %s, is_resolved = %s WHERE alert_id = %s",
            (data.get('severity_level'), data.get('is_resolved', 0), alert_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Update fraud alert error: {e}")
        return jsonify({'error': 'Failed to update alert'}), 500

@security_bp.route('/fraud-alerts', methods=['POST'])
def create_fraud_alert():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO fraud_alerts (user_id, transaction_id, severity_level, is_resolved) VALUES (%s, %s, %s, %s)",
            (data.get('user_id'), data.get('transaction_id'), data.get('severity_level', 'Medium'), 0)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True}), 201
    except Exception as e:
        print(f"Create fraud alert error: {e}")
        return jsonify({'error': 'Failed to create alert'}), 500

# ==================== TRUSTED DEVICES ====================
@security_bp.route('/trusted-devices', methods=['GET'])
def get_trusted_devices():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT td.*, dr.device_type FROM trusted_devices td LEFT JOIN device_registry dr ON td.device_fingerprint = dr.device_fingerprint WHERE td.user_id = %s",
            (user_id,)
        )
        devices = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': devices}), 200
    except Exception as e:
        print(f"Get trusted devices error: {e}")
        return jsonify({'error': 'Failed to fetch devices'}), 500

@security_bp.route('/trusted-devices', methods=['POST'])
def add_trusted_device():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(device_id) FROM trusted_devices")
        device_id = (cursor.fetchone()[0] or 0) + 1
        
        cursor.execute(
            "INSERT INTO trusted_devices (device_id, user_id, device_fingerprint, last_used_at) VALUES (%s, %s, %s, NOW())",
            (device_id, data['user_id'], data['device_fingerprint'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'device_id': device_id}), 201
    except Exception as e:
        print(f"Add trusted device error: {e}")
        return jsonify({'error': 'Failed to add device'}), 500

@security_bp.route('/trusted-devices/<int:device_id>', methods=['DELETE'])
def remove_trusted_device(device_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trusted_devices WHERE device_id = %s", (device_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Remove trusted device error: {e}")
        return jsonify({'error': 'Failed to remove device'}), 500

# ==================== SECURITY QUESTIONS ====================
@security_bp.route('/security-questions', methods=['GET'])
def get_security_questions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT question_id, question_text, difficulty_level FROM security_question_bank ORDER BY question_id")
        questions = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': questions}), 200
    except Exception as e:
        print(f"Get security questions error: {e}")
        return jsonify({'error': 'Failed to fetch questions'}), 500

@security_bp.route('/user-security-questions', methods=['GET'])
def get_user_security_questions():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT usq.security_id, usq.question_id, sq.question_text FROM user_security_questions usq LEFT JOIN security_question_bank sq ON usq.question_id = sq.question_id WHERE usq.user_id = %s",
            (user_id,)
        )
        questions = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': questions}), 200
    except Exception as e:
        print(f"Get user security questions error: {e}")
        return jsonify({'error': 'Failed to fetch user questions'}), 500

@security_bp.route('/user-security-questions', methods=['POST'])
def set_user_security_question():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(security_id) FROM user_security_questions")
        security_id = (cursor.fetchone()[0] or 0) + 1
        
        cursor.execute(
            "INSERT INTO user_security_questions (security_id, user_id, question_id, answer_hash) VALUES (%s, %s, %s, %s)",
            (security_id, data['user_id'], data['question_id'], data['answer_hash'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'security_id': security_id}), 201
    except Exception as e:
        print(f"Set user security question error: {e}")
        return jsonify({'error': 'Failed to set security question'}), 500

# ==================== LOGIN SESSIONS ====================
@security_bp.route('/login-sessions', methods=['GET'])
def get_login_sessions():
    try:
        user_id = request.args.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if user_id:
            cursor.execute(
                "SELECT * FROM login_sessions WHERE user_id = %s ORDER BY login_time DESC LIMIT 20",
                (user_id,)
            )
        else:
            cursor.execute("SELECT * FROM login_sessions ORDER BY login_time DESC LIMIT 50")
        
        sessions = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': sessions}), 200
    except Exception as e:
        print(f"Get login sessions error: {e}")
        return jsonify({'error': 'Failed to fetch sessions'}), 500

@security_bp.route('/login-sessions/<int:session_id>', methods=['PUT'])
def update_login_session(session_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE login_sessions SET logout_time = NOW(), session_token = %s WHERE session_id = %s",
            (data.get('session_token'), session_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Update login session error: {e}")
        return jsonify({'error': 'Failed to update session'}), 500

# ==================== ACTIVITY LOGS ====================
@security_bp.route('/activity-logs', methods=['GET'])
def get_activity_logs():
    try:
        session_id = request.args.get('session_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if session_id:
            cursor.execute(
                "SELECT * FROM activity_logs WHERE session_id = %s ORDER BY timestamp DESC",
                (session_id,)
            )
        else:
            cursor.execute("SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 100")
        
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': logs}), 200
    except Exception as e:
        print(f"Get activity logs error: {e}")
        return jsonify({'error': 'Failed to fetch logs'}), 500

# ==================== BANK ACCOUNTS ====================
@security_bp.route('/bank-accounts', methods=['GET'])
def get_bank_accounts():
    try:
        user_id = request.args.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if user_id:
            cursor.execute("SELECT * FROM bank_accounts WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("SELECT * FROM bank_accounts")
        
        accounts = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': accounts}), 200
    except Exception as e:
        print(f"Get bank accounts error: {e}")
        return jsonify({'error': 'Failed to fetch accounts'}), 500

@security_bp.route('/bank-accounts/<int:account_number>', methods=['PUT'])
def update_bank_account(account_number):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        for field in ['balance', 'status', 'account_type']:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        
        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(account_number)
        query = f"UPDATE bank_accounts SET {', '.join(updates)} WHERE account_number = %s"
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Update bank account error: {e}")
        return jsonify({'error': 'Failed to update account'}), 500

# ==================== FAILED LOGIN ATTEMPTS ====================
@security_bp.route('/failed-logins', methods=['GET'])
def get_failed_logins():
    try:
        user_id = request.args.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if user_id:
            cursor.execute(
                "SELECT * FROM failed_login_attempts WHERE user_id = %s ORDER BY attempt_time DESC LIMIT 20",
                (user_id,)
            )
        else:
            cursor.execute("SELECT * FROM failed_login_attempts ORDER BY attempt_time DESC LIMIT 100")
        
        attempts = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': attempts}), 200
    except Exception as e:
        print(f"Get failed logins error: {e}")
        return jsonify({'error': 'Failed to fetch attempts'}), 500
