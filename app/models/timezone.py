from app import db
from app.models.base import BaseModel

class TimeZone(BaseModel):
    """
    TimeZone model for storing time zone information
    """
    __tablename__ = 'time_zones'

    name = db.Column(db.String(100), nullable=False)
    offset = db.Column(db.String(10), nullable=False)

    def to_dict(self):
        """Convert timezone object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'offset': self.offset,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 