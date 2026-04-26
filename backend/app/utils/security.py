import hashlib
import secrets
from functools import wraps
from flask import request, jsonify

def hash_password(password):
    """Hash password using SHA-256 (note: use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_input(value, input_type='string', max_length=255):
    """Validate and sanitize user input"""
    if input_type == 'string':
        if not isinstance(value, str) or len(value) > max_length:
            return False
        return True
    elif input_type == 'email':
        return '@' in value and '.' in value and len(value) < max_length
    elif input_type == 'phone':
        return value.isdigit() and 10 <= len(value) <= 15
    elif input_type == 'int':
        try:
            int(value)
            return True
        except:
            return False
    return False

def require_auth(f):
    """Decorator for authenticated endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.headers.get('X-Session-Id')
        if not session_id:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)
