from app import db
from datetime import datetime
from app.models.base import BaseModel

class Product(BaseModel):
    __tablename__ = 'products'
    
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    shopify_product_id = db.Column(db.BigInteger, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    vendor = db.Column(db.String(255))
    product_type = db.Column(db.String(255))
    handle = db.Column(db.String(255))
    status = db.Column(db.String(50), default='active')
    shopify_created_at = db.Column(db.DateTime)
    shopify_updated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with Store
    store = db.relationship('Store', backref=db.backref('products', lazy=True))
    
    # Relationship with OptimizedDescription
    optimized_descriptions = db.relationship('OptimizedDescription', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'store_id': self.store_id,
            'shopify_product_id': self.shopify_product_id,
            'title': self.title,
            'description': self.description,
            'vendor': self.vendor,
            'product_type': self.product_type,
            'handle': self.handle,
            'status': self.status,
            'shopify_created_at': self.shopify_created_at.isoformat() if self.shopify_created_at else None,
            'shopify_updated_at': self.shopify_updated_at.isoformat() if self.shopify_updated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }