from datetime import datetime
from sqlalchemy import event
from .. import db

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating from 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, product_id, user_id, rating, comment=None):
        self.product_id = product_id
        self.user_id = user_id
        self.rating = min(max(rating, 1), 5)  # Ensure rating is between 1 and 5
        self.comment = comment

    @staticmethod
    def on_change(target, value, oldvalue, initiator):
        """SQLAlchemy event listener to update product rating when a review is changed"""
        if target.product:
            target.product.update_rating()

    @staticmethod
    def on_delete(target):
        """SQLAlchemy event listener to update product rating when a review is deleted"""
        if target.product:
            db.session.expire(target.product, ['reviews'])
            target.product.update_rating()

# Register SQLAlchemy event listeners
event.listen(Review.rating, 'set', Review.on_change)
event.listen(Review, 'after_delete', Review.on_delete)
