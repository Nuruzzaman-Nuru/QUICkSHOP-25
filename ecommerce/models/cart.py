from datetime import datetime
from .. import db

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    negotiated_price = db.Column(db.Float)  # Price after successful negotiation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')
    
    def __init__(self, user_id, product_id, quantity=1, negotiated_price=None):
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.negotiated_price = negotiated_price
    
    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        unit_price = self.negotiated_price or self.product.price
        return unit_price * self.quantity
    
    def to_dict(self):
        """Convert cart item to dictionary"""
        return {
            'id': self.id,
            'product': self.product.to_dict(),
            'quantity': self.quantity,
            'unit_price': self.negotiated_price or self.product.price,
            'total_price': self.total_price,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }