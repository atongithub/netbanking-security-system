from flask import Blueprint, request, jsonify
from app.utils import get_db_connection, format_datetime_fields

crud_bp = Blueprint('crud', __name__, url_prefix='/api')

ALLOWED_TABLES = [
    'users', 'bank_accounts', 'bank_details', 'login_sessions', 
    'activity_logs', 'transactions', 'beneficiaries', 'failed_login_attempts',
    'device_registry', 'trusted_devices', 'otp_validation', 
    'security_question_bank', 'user_security_questions', 
    'alert_severity_master', 'fraud_alerts'
]

DATETIME_FIELDS = ['last_used_at', 'timestamp', 'attempt_time', 'created_at', 'updated_at', 'login_time', 'logout_time']

@crud_bp.route('/admin/tables', methods=['GET'])
def get_tables():
    """Get list of all tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = (SELECT DATABASE())
            ORDER BY TABLE_NAME
        """)
        
        tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'tables': tables}), 200
    except Exception as e:
        print(f"Get tables error: {e}")
        return jsonify({'error': 'Database error'}), 500

@crud_bp.route('/admin/table/<table_name>', methods=['GET'])
def get_table_data(table_name):
    """Get all data from a specific table"""
    try:
        if table_name not in ALLOWED_TABLES:
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

@crud_bp.route('/admin/table/<table_name>/<row_id>', methods=['PUT'])
def update_table_row(table_name, row_id):
    """Update a row in a table"""
    try:
        if table_name not in ALLOWED_TABLES:
            return jsonify({'error': 'Invalid table'}), 400
        
        data = request.json
        data = format_datetime_fields(data, DATETIME_FIELDS)
        
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
        return jsonify({'error': f'Update failed: {str(e)}'}), 500

@crud_bp.route('/admin/table/<table_name>', methods=['POST'])
def insert_table_row(table_name):
    """Insert a new row into a table"""
    try:
        if table_name not in ALLOWED_TABLES:
            return jsonify({'error': 'Invalid table'}), 400
        
        data = request.json
        data = format_datetime_fields(data, DATETIME_FIELDS)
        
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
        return jsonify({'error': f'Insert failed: {str(e)}'}), 500

@crud_bp.route('/admin/table/<table_name>/<row_id>', methods=['DELETE'])
def delete_table_row(table_name, row_id):
    """Delete a row from a table"""
    try:
        if table_name not in ALLOWED_TABLES:
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
