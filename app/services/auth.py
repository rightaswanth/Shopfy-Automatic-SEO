from functools import wraps
from flask import g

from app.services.crud import CRUD
from app.services.custom_errors import NoContent, Forbidden
from app.models import User
from app.services.user import upload_user_profile_pic


class AuthService(object):
    @staticmethod
    def forgot_password(email: str, expires_in=3600) -> tuple:
        """
        Generate a password reset token for a user
        """
        user = User.query.filter_by(email=email, is_active=True).first()
        if not user:
            raise NoContent("Please enter a valid email address.")
        
        token = user.generate_auth_token(expires_in)
        return user.name, token

    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """
        Reset a user's password using a token
        """
        user = User.verify_auth_token(token)
        if not user:
            raise Forbidden("Invalid or expired token")
        
        user.hash_password(new_password)
        CRUD.db_commit()
        return True

    @staticmethod
    def update_password(user_id: int, current_password: str, new_password: str) -> bool:
        """
        Update a user's password after verifying the current password
        """
        user = User.query.get(user_id)
        if not user:
            raise NoContent("User not found")
        
        if not user.check_password(current_password):
            raise Forbidden("Current password is incorrect")
        
        user.hash_password(new_password)
        CRUD.db_commit()
        return True


def admin_authorizer(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if not g.current_user.is_admin:
            raise Forbidden("Admin access required")
        return func(*args, **kwargs)
    return inner
