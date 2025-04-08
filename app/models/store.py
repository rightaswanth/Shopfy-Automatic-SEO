from app import db
from app.models.base import BaseModel

class Store(BaseModel):
    """
    Store model for managing Shopify stores
    """
    __tablename__ = 'stores'

    store_url = db.Column(db.String(255), unique=True, nullable=False)
    access_token = db.Column(db.String(255), nullable=False)
    store_name = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship with User model
    user = db.relationship('User', backref=db.backref('stores', lazy=True))

    def __init__(self, store_url, access_token, user_id, store_name=None):
        self.store_url = store_url
        self.access_token = access_token
        self.user_id = user_id
        self.store_name = store_name

    def to_dict(self):
        """Convert store object to dictionary"""
        return {
            'id': self.id,
            'store_url': self.store_url,
            'store_name': self.store_name,
            'user_id': self.user_id,
            'access_token': self.access_token,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 