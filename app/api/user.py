"""API Endpoints related to User profile management."""

from flask import request, jsonify, g
from app.api import bp
from app.services.auth import AuthService
from .auth import tokenAuth
from app.services.custom_errors import BadRequest
from app.models import User
from app.services import user_avatar_uploading, user_avatar_deleting
from config import Config_is
from app.services.crud import CRUD

auth_service = AuthService()

@bp.route('/user/profile', methods=['GET'])
@tokenAuth.login_required
def get_user_profile():
    """
    Get the current user's profile
    """
    user = g.current_user
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'avatar_url': user.avatar_url,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None
    }), 200

@bp.route('/user/profile', methods=['PUT'])
@tokenAuth.login_required
def update_user_profile():
    """
    Update the current user's profile
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided', 'status': 400}), 400
    
    # Only allow updating specific fields
    allowed_fields = ['name', 'email']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return jsonify({'message': 'No valid fields to update', 'status': 400}), 400
    
    # Update user profile
    CRUD.update(User, {'id': g.current_user.id}, update_data)
    
    return jsonify({'message': 'Profile updated successfully', 'status': 200}), 200

@bp.route('/user/password', methods=['PUT'])
@tokenAuth.login_required
def update_password():
    """
    Update the current user's password
    """
    data = request.get_json()
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({'message': 'Missing required fields', 'status': 400}), 400
    
    user = g.current_user
    
    # Verify current password
    if not user.check_password(data['current_password']):
        return jsonify({'message': 'Current password is incorrect', 'status': 400}), 400
    
    # Update password
    user.hash_password(data['new_password'])
    CRUD.db_commit()
    
    return jsonify({'message': 'Password updated successfully', 'status': 200}), 200

@bp.route('/user/avatar', methods=['PUT', 'DELETE'])
@tokenAuth.login_required
def manage_avatar():
    """
    Update or delete the current user's avatar
    """
    if request.method == 'DELETE':
        user_avatar_deleting()
        return jsonify({'message': 'Avatar deleted successfully', 'status': 200}), 200
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided', 'status': 400}), 400
    
    avatar = user_avatar_uploading(request.files)
    return jsonify({
        'data': f"https://{Config_is.S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com/{g.current_user.id}/avatar/{avatar}",
        'message': 'Avatar updated successfully', 
        'status': 200
    }), 200
