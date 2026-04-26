import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

from app import create_app
from app.utils import test_connection

if __name__ == '__main__':
    # Test database connection before starting server
    print("Testing database connection...")
    if not test_connection():
        print("❌ Failed to connect to database. Please check your configuration.")
        sys.exit(1)
    
    print("✅ Database connection successful!")
    
    # Create and run Flask app
    app = create_app()
    
    print("🚀 Starting Flask server on http://0.0.0.0:5000")
    print("📝 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
