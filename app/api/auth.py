"""Authentication module for API endpoints."""

from flask import request, g, jsonify, Blueprint
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, create_access_token
from functools import wraps
from app.models import User
from app.services.custom_errors import Unauthorized, BadRequest
from app.services.crud import CRUD
from app.services.auth import AuthService
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# Create a Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

class TokenAuth:
    """Token authentication class for API endpoints."""
    
    def login_required(self, f):
        """Decorator to require JWT token authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            # Use CRUD to get user
            user = User.query.get(user_id)
            if not user:
                raise Unauthorized("User not found")
            g.current_user = user
            return f(*args, **kwargs)
        return decorated_function

# Create a singleton instance
tokenAuth = TokenAuth()

# Create a token_required decorator for backward compatibility
def token_required(f):
    """Decorator to require JWT token authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        # Use CRUD to get user
        user = User.query.get(user_id)
        if not user:
            raise Unauthorized("User not found")
        g.current_user = user
        return f(user, *args, **kwargs)
    return decorated_function

# Add authentication routes
@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if not data or not data.get(field):
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    # Check if user already exists using raw SQL
    from app import db
    result = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": data.get('email')})
    if result.first():
        return jsonify({"message": "Email already registered"}), 409
    
    # Create new user
    user_data = {
        'name': data.get('name'),
        'email': data.get('email'),
        'password': data.get('password'),
        'is_active': True,
        'registered': True
    }
    
    try:
        new_user = User(
            name=user_data['name'],
            email=user_data['email'],
            password=user_data['password']
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Generate access token
        access_token = create_access_token(identity=new_user.id)
        
        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error registering user: {str(e)}"}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint to authenticate users."""
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Missing email or password"}), 400
    
    # Use CRUD to find user
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not user.check_password(data.get('password')):
        return jsonify({"message": "Invalid email or password"}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@tokenAuth.login_required
def refresh():
    """Refresh token endpoint."""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": access_token}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request a password reset token."""
    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({"message": "Missing email"}), 400
    
    try:
        name, token = AuthService.forgot_password(data.get('email'))
        # In a real application, you would send this token via email
        # For development, we'll return it in the response
        return jsonify({
            "message": "Password reset token generated",
            "token": token
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using a token."""
    data = request.get_json()
    if not data or not data.get('token') or not data.get('password'):
        return jsonify({"message": "Missing token or password"}), 400
    
    try:
        AuthService.reset_password(data.get('token'), data.get('password'))
        return jsonify({"message": "Password reset successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400 