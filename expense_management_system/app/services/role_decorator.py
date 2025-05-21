from functools import wraps
from flask import jsonify, g
from app.services.auth_decorator import token_required

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        @token_required # Ensures user is logged in first
        def decorated_function(*args, **kwargs):
            if not g.current_user.role or g.current_user.role.name != role_name:
                return jsonify({'message': f'Access denied: Requires {role_name} role'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
