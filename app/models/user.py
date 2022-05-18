import json
from datetime import timedelta
import pytz
import redis
from flask_httpauth import HTTPBasicAuth
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from .base import BaseModel
from config import Config_is

auth = HTTPBasicAuth()
redis_obj = redis.StrictRedis.from_url(Config_is.REDIS_URL, decode_responses=True)


class User(BaseModel):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)

    # Credential
    email = db.Column(db.String(50), index=True, unique=True, nullable=False)
    hashed_password = db.Column(db.Text)
    # User information
    first_name = db.Column(db.String(60))
    last_name = db.Column(db.String(60))
    role_id = db.Column(db.Integer, default=3, index=True, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    avatar = db.Column(db.String(120))
    # User state
    is_invited = db.Column(db.Boolean, default=False)
    registered = db.Column(db.Boolean, default=False)

    # Relationships
    organization = db.relationship("Organization", viewonly=True, backref="user_in_organization", uselist=False)

    def login_to_dict(self):
        """
        Logged-in user info from object to dict
        """
        data = dict(
            id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            role_id=self.role_id,
            organization={'id': self.organization_id, 'name': self.organization.name,
                          'services': json.loads(self.organization.services)},
            avatar=f"https://{Config_is.S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com/{self.organization_id}/avatar/"
                   f"{self.avatar}" if self.avatar else None,
        )
        return data

    def to_dict(self, tz: str):
        """Convert table object to dictionary."""
        data = dict(
            id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            is_active=self.is_active,
            is_invited=self.is_invited,
            registered=self.registered,
            role_id=self.role_id,
            avatar=f"https://{Config_is.S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com/{self.organization_id}/avatar/"
                   f"{self.avatar}" if self.avatar else None,
            updated_at=self.updated_at.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz)).strftime(
                "%Y-%m-%d %H:%M:%S"),
            created_at=self.created_at.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz)).strftime(
                "%Y-%m-%d %H:%M:%S")
        )
        return data

    def basic_to_dict(self):
        data = dict(
            id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            avatar=f"https://{Config_is.S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com/{self.organization_id}/avatar/"
                   f"{self.avatar}" if self.avatar else None
        )
        return data

    def get_hashed_password(self, password):
        return generate_password_hash(password)

    def hash_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def generate_auth_token(self, expiration=Config_is.AUTH_TOKEN_EXPIRES):
        s = URLSafeTimedSerializer(Config_is.SECRET_KEY)
        token = s.dumps({'id': self.id, 'role_id': self.role_id, 'organization_id': self.organization_id})
        add_user_token_in_cache(self.id, expiration, token)
        return token

    @staticmethod
    def verify_auth_token(token: str, expires_in: int = Config_is.AUTH_TOKEN_EXPIRES):
        serializer = URLSafeTimedSerializer(Config_is.SECRET_KEY)
        try:
            data = serializer.loads(token, max_age=expires_in)
            if verify_user_token_in_cache(data['id'], token):
                return data
        except Exception as e:
            print(e)
        return False


def add_user_token_in_cache(user_id: int, expiry_at: int, user_auth_token: str) -> bool:
    redis_obj.setex(user_id, timedelta(seconds=expiry_at), user_auth_token)
    return True


def verify_user_token_in_cache(user_id: int, user_auth_token: str):
    if redis_obj.get(user_id) == user_auth_token:
        return True
    return False


def remove_user_token(user_id: int, user_auth_token: str = None):
    if redis_obj.get(user_id) == user_auth_token or not user_auth_token:
        redis_obj.delete(user_id)
    return True
