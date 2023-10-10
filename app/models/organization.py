"""Models for defining the organization details."""

import json

from app import db
from .base import BaseModel


class Organization(BaseModel):
    """Table for defining the organization details"""
    __tablename__ = "organization"
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    domain = db.Column(db.String(40), nullable=False, unique=True, index=True)
    services = db.Column(db.Text, default=json.dumps([]))
    members = db.relationship("User", backref="organization_users", lazy=True)

    def to_dict(self):
        """Convert table object to dictionary."""
        data = dict(
            id=self.id,
            name=self.name,
            domain=self.domain,
            services=json.loads(self.services)
        )
        return data
