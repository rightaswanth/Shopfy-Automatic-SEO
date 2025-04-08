from app import db
from datetime import datetime
import enum
from app.models.base import BaseModel

class DescriptionStatus(enum.Enum):
    DRAFT = 'draft'
    DEPLOYED = 'deployed'

class OptimizedDescription(BaseModel):
    __tablename__ = 'optimized_descriptions'
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    original_description = db.Column(db.Text)
    optimized_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(DescriptionStatus), default=DescriptionStatus.DRAFT, nullable=False)
    
    def __repr__(self):
        return f'<OptimizedDescription {self.id} for Product {self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'original_description': self.original_description,
            'optimized_description': self.optimized_description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 