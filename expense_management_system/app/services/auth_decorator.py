from functools import wraps
from flask import request, jsonify, g # g is Flask's application context global
from app.services.auth_service import decode_token
from app.models.user import User

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            user_id = decode_token(token)
            if isinstance(user_id, str) and ("Token expired" in user_id or "Invalid token" in user_id): # Check if decode_token returned an error message
                return jsonify({'message': user_id}), 401
            
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            g.current_user = current_user # Store user in Flask's g object for access in route
        except Exception as e:
            return jsonify({'message': 'Token is invalid or expired!', 'error': str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated_function
