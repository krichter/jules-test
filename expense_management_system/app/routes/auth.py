from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.models.role import Role # Import Role model
from app.services.auth_service import generate_token
# passlib is already used in the User model for hashing, so no need to import it directly here for that.

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing username, email, or password'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400

    # Assign a default role, e.g., 'employee'
    # This assumes you have a way to create roles, perhaps a seed script or admin interface later
    # For now, let's try to find 'employee' role or create if not exists for simplicity in this step
    employee_role = Role.query.filter_by(name='employee').first()
    if not employee_role:
        # This is a simplistic way to handle it; ideally, roles are pre-populated
        employee_role = Role(name='employee')
        db.session.add(employee_role)
        # If we add here, we should commit. Or, better, ensure roles are seeded.
        # For now, let's assume roles might need to be created on the fly if not present.
        # db.session.commit() # This could be problematic if other operations fail.
                            # Better to ensure roles exist or handle this more robustly.
                            # For this subtask, we'll proceed assuming it might be created.
                            # A proper seeding step would be better.

    new_user = User(
        username=data['username'],
        email=data['email'],
        role=employee_role # Assign the role
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # If role creation was attempted and not committed, it would also be rolled back.
        return jsonify({'message': 'Failed to register user', 'error': str(e)}), 500
        
    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user and user.check_password(data['password']):
        token = generate_token(user.id)
        return jsonify({'token': token}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401
