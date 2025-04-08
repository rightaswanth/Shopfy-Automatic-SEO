from datetime import datetime, timedelta
from typing import Optional, Tuple
from app.models.user import User
from app import db
from flask import current_app
import jwt

class AuthService:
    @staticmethod
    def register_user(email: str, password: str) -> Tuple[bool, str]:
        """
        Register a new user
        Returns: (success: bool, message: str)
        """
        if User.query.filter_by(email=email).first():
            return False, "Email already registered"

        try:
            user = User(
                email=email,
                password=password
            )
            db.session.add(user)
            db.session.commit()
            return True, "User registered successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}"

    @staticmethod
    def login_user(email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Authenticate user and return token
        Returns: (success: bool, message: str, data: Optional[dict])
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return False, "User not found", None
        
        if not user.check_password(password):
            return False, "Invalid password", None

        token = AuthService.generate_token(user)
        return True, "Login successful", {
            'token': token,
            'user': user.to_dict()
        }

    @staticmethod
    def generate_token(user: User, expires_in: int = 3600) -> str:
        """
        Generate JWT token for user
        """
        payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_token(token: str) -> Tuple[bool, Optional[dict]]:
        """
        Verify JWT token
        Returns: (valid: bool, payload: Optional[dict])
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None 