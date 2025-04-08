import json
from datetime import timedelta, datetime
import pytz
import redis
from flask_httpauth import HTTPBasicAuth
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, redis_obj
from app.models.base import BaseModel
from config import Config_is

auth = HTTPBasicAuth()


class User(BaseModel):
    """
    User model for authentication and user management
    """
    __tablename__ = 'users'

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    registered = db.Column(db.Boolean, default=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)

    def __init__(self, name, email, password=None, password_hash=None, organization_id=None):
        self.name = name
        self.email = email
        self.organization_id = organization_id
        if password:
            self.set_password(password)
        elif password_hash:
            self.password_hash = password_hash

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, tz: str = 'UTC'):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_active': self.is_active,
            'registered': self.registered,
            'organization_id': self.organization_id,
            'created_at': self.created_at.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz)).strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'updated_at': self.updated_at.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz)).strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }

    def login_to_dict(self):
        """
        Logged-in user info from object to dict
        """
        data = dict(
            id=self.id,
            name=self.name,
            email=self.email,
            organization_id=self.organization_id,
            is_active=self.is_active
        )
        return data

    def generate_auth_token(self, expiration: int = Config_is.AUTH_TOKEN_EXPIRES):
        """
        Generate user token and store the value in redis
        """
        s = URLSafeTimedSerializer(Config_is.SECRET_KEY)
        token = s.dumps(
            {'id': self.id, 'name': self.name, 'email': self.email})
        add_user_token_in_cache(self.id, expiration, token)
        return token

    @staticmethod
    def verify_auth_token(token: str, expires_in: int = Config_is.AUTH_TOKEN_EXPIRES):
        """
        Verifying the user token valid or not
        """
        serializer = URLSafeTimedSerializer(Config_is.SECRET_KEY)
        try:
            data = serializer.loads(token, max_age=expires_in)
            if verify_user_token_in_cache(data['id'], token):
                return data
        except Exception as e:
            print(e)
        return False


def add_user_token_in_cache(user_id: int, expiry_at: int, user_auth_token: str) -> bool:
    redis_obj.setex(f"{user_id}", timedelta(seconds=expiry_at), user_auth_token)
    return True


def verify_user_token_in_cache(user_id: int, user_auth_token: str):
    if redis_obj.get(f"{user_id}") == user_auth_token:
        return True
    return False


def remove_user_token(user_id: int, user_auth_token: str = None):
    """
    Remove user token from redis
    """
    if redis_obj.get(f"{user_id}") == user_auth_token or not user_auth_token:
        redis_obj.delete(f"{user_id}")
    return True
