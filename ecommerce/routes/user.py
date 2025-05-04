from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from ..models.order import Order
from ..models.shop import Shop
from ..models.user import User
from ..models.cart import CartItem
from ..models.negotiation import Negotiation
from ..utils.notifications import notify_customer_order_status, notify_admin_order_status
from ..utils.ai.negotiation_bot import process_negotiation
from datetime import datetime
from .. import db

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    # Get active orders
    active_orders = Order.query.filter(
        Order.customer_id == current_user.id,
        Order.status.in_(['pending', 'confirmed', 'delivering'])
    ).all()
    active_orders_count = len(active_orders)
    
    # Get cart items count
    cart_items_count = db.session.query(func.count(CartItem.id))\
        .filter_by(user_id=current_user.id)\
        .scalar() or 0
    
    # Get pending negotiations
    pending_negotiations = Negotiation.query.filter(
        Negotiation.customer_id == current_user.id,
        Negotiation.status.in_(['pending', 'counter_offer'])
    ).all()
    pending_negotiations_count = len(pending_negotiations)
    
    # Get recent orders
    recent_orders = Order.query.filter_by(customer_id=current_user.id)\
        .order_by(Order.created_at.desc())\
        .limit(5).all()
    
    # Get active negotiations
    active_negotiations = Negotiation.query.filter(
        Negotiation.customer_id == current_user.id,
        Negotiation.status != 'completed'
    ).all()
    
    # Get nearby shops if user has location
    nearby_shops = []
    if current_user.location_lat and current_user.location_lng:
        shops = Shop.query.filter_by(is_active=True).all()
        for shop in shops:
            if shop.location_lat and shop.location_lng:
                shop.distance = calculate_distance(
                    current_user.location_lat,
                    current_user.location_lng,
                    shop.location_lat,
                    shop.location_lng
                )
                if shop.distance <= 10:  # Only show shops within 10km
                    nearby_shops.append(shop)
        nearby_shops.sort(key=lambda x: x.distance)
    
    return render_template('user/dashboard.html',
                         active_orders_count=active_orders_count,
                         cart_items_count=cart_items_count,
                         pending_negotiations_count=pending_negotiations_count,
                         recent_orders=recent_orders,
                         active_negotiations=active_negotiations,
                         nearby_shops=nearby_shops[:6])  # Limit to 6 shops

@user_bp.route('/orders')
@login_required
def orders():
    status = request.args.get('status', None)
    query = Order.query.filter_by(customer_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
        
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('user/orders.html', orders=orders)

@user_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('user.orders'))
    return render_template('user/order_detail.html', order=order)

@user_bp.route('/track-order/<int:order_id>')
@login_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('user.orders'))
    return render_template('user/track_order.html', order=order)

@user_bp.route('/negotiations')
@login_required
def negotiations():
    negotiations = Negotiation.query.filter_by(customer_id=current_user.id)\
        .order_by(Negotiation.created_at.desc()).all()
    return render_template('user/negotiations.html', negotiations=negotiations)

@user_bp.route('/negotiation/<int:nego_id>')
@login_required
def negotiation_detail(nego_id):
    negotiation = Negotiation.query.get_or_404(nego_id)
    if negotiation.customer_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('user.negotiations'))
    return render_template('user/negotiation_detail.html', negotiation=negotiation)

@user_bp.route('/negotiation/<int:nego_id>/counter', methods=['POST'])
@login_required
def make_counter_offer(nego_id):
    negotiation = Negotiation.query.get_or_404(nego_id)
    if negotiation.customer_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'Access denied'
        }), 403
        
    offered_price = float(request.form.get('offered_price', 0))
    if offered_price <= 0:
        return jsonify({
            'status': 'error',
            'message': 'Invalid price'
        }), 400
        
    # Process negotiation with AI
    result = process_negotiation(negotiation, offered_price)
    if result['accepted']:
        negotiation.status = 'accepted'
        negotiation.final_price = offered_price
    else:
        negotiation.status = 'counter_offer'
        negotiation.counter_price = result['counter_price']
    
    negotiation.offered_price = offered_price
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'result': result
    })

@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        address = request.form.get('address')
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        
        try:
            current_user.address = address
            current_user.location_lat = float(lat) if lat else None
            current_user.location_lng = float(lng) if lng else None
            db.session.commit()
            flash('Settings updated successfully!', 'success')
        except ValueError:
            flash('Invalid coordinates provided.', 'error')
            
    return render_template('user/settings.html')

@user_bp.route('/nearby-shops')
@login_required
def nearby_shops():
    if not current_user.location_lat or not current_user.location_lng:
        flash('Please update your location in settings.', 'warning')
        return redirect(url_for('user.settings'))
        
    shops = Shop.query.filter_by(is_active=True).all()
    for shop in shops:
        if shop.location_lat and shop.location_lng:
            shop.distance = calculate_distance(
                current_user.location_lat,
                current_user.location_lng,
                shop.location_lat,
                shop.location_lng
            )
        else:
            shop.distance = float('inf')
    
    # Sort shops by distance
    shops.sort(key=lambda x: x.distance)
    
    return render_template('user/nearby_shops.html', shops=shops)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance