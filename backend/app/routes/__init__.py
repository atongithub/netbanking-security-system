from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.crud import crud_bp
from app.routes.user import user_bp
from app.routes.security import security_bp

__all__ = ['auth_bp', 'admin_bp', 'crud_bp', 'user_bp', 'security_bp']
