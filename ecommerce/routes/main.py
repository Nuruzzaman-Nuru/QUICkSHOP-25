from flask import Blueprint, render_template, session, send_from_directory
from flask_login import login_required
from ..models.shop import Shop, Product
from .api import init_cart

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_shops = Shop.query.filter_by(is_active=True).limit(6).all()
    return render_template('main/home.html', featured_shops=featured_shops)

@main_bp.route('/checkout')
@login_required
def checkout():
    init_cart()
    cart = session.get('cart', {})
    if not cart:
        return render_template('main/checkout.html', cart_items=[])
    
    cart_items = []
    total = 0
    for product_id, item in cart.items():
        product = Product.query.get(product_id)
        if product:
            subtotal = item['quantity'] * item['price']
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'price': item['price'],
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('main/checkout.html', cart_items=cart_items, total=total)

@main_bp.route('/cart')
@login_required
def cart():
    init_cart()
    return render_template('main/cart.html')

@main_bp.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)

@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500