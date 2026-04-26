import os
from mysql.connector import Error
import mysql.connector

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'netbankinglogging'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Database error: {e}")
        return None

def test_connection():
    """Test database connection on startup"""
    try:
        conn = get_db_connection()
        if conn:
            print("✓ MySQL database connection successful")
            conn.close()
            return True
        else:
            print("✗ MySQL connection failed")
            return False
    except Exception as e:
        print(f"✗ MySQL connection failed: {e}")
        return False
