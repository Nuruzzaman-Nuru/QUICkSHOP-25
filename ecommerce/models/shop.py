from datetime import datetime
from .. import db

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location_lat = db.Column(db.Float, nullable=False)
    location_lng = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    products = db.relationship('Product', backref='shop', lazy=True)
    orders = db.relationship('Order', backref='shop', lazy=True)

    def __init__(self, name, description, owner_id, location_lat, location_lng, address):
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.location_lat = location_lat
        self.location_lng = location_lng
        self.address = address

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'location': {
                'lat': self.location_lat,
                'lng': self.location_lng,
                'address': self.address
            },
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    image_url = db.Column(db.String(255))
    category = db.Column(db.String(50))  # Add category field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Negotiation settings
    min_price = db.Column(db.Float)  # Minimum acceptable price
    max_discount_percentage = db.Column(db.Float, default=20.0)  # Maximum allowed discount
    continue_iteration = db.Column(db.Boolean, default=False)  # Whether to continue negotiation after max discount
    
    def __init__(self, name, description, price, stock, shop_id, min_price=None, max_discount_percentage=20.0, image_url=None, continue_iteration=False, category=None):
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock
        self.shop_id = shop_id
        self.min_price = min_price
        self.max_discount_percentage = max_discount_percentage
        self.image_url = image_url
        self.continue_iteration = continue_iteration
        self.category = category

    def is_negotiable(self):
        """Check if product supports price negotiation"""
        return self.min_price is not None and self.min_price < self.price

    def can_negotiate_price(self, offered_price):
        """Check if an offered price is within acceptable range"""
        if not self.is_negotiable():
            return False
        
        discount = (self.price - offered_price) / self.price * 100
        return offered_price >= self.min_price and discount <= self.max_discount_percentage

    def update_stock(self, quantity_change):
        """Update product stock, return True if successful"""
        new_stock = self.stock + quantity_change
        if new_stock < 0:
            return False
        self.stock = new_stock
        return True

    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'shop_id': self.shop_id,
            'shop_name': self.shop.name,
            'image_url': self.image_url,
            'category': self.category,
            'is_negotiable': self.is_negotiable(),
            'min_price': self.min_price if self.is_negotiable() else None,
            'max_discount': self.max_discount_percentage if self.is_negotiable() else None,
            'created_at': self.created_at.isoformat()
        }