from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, or_, and_, desc, asc, cast, String, case
from ..models.order import Order, OrderItem
from ..models.shop import Shop, Product
from ..models.user import User
from ..models.cart import CartItem
from ..models.negotiation import Negotiation
from ..utils.notifications import notify_customer_order_status, notify_admin_order_status
from ..utils.ai.negotiation_bot import process_negotiation
from datetime import datetime
from .. import db
from ..routes.auth import customer_required

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
@customer_required
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
@customer_required
def orders():
    # Get search and filter parameters
    search_query = request.args.get('q', '')
    status = request.args.get('status')
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Base query
    query = Order.query.filter_by(customer_id=current_user.id)
    
    # Apply search filter
    if search_query:
        query = query.join(Order.shop).join(Order.items).join(OrderItem.product).filter(
            or_(
                Order.id.cast(String).ilike(f'%{search_query}%'),
                Shop.name.ilike(f'%{search_query}%'),
                Product.name.ilike(f'%{search_query}%')
            )
        ).distinct()
    
    # Apply status filter
    if status:
        query = query.filter_by(status=status)
    
    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(Order.created_at.asc())
    elif sort == 'highest':
        query = query.order_by(Order.total_amount.desc())
    elif sort == 'lowest':
        query = query.order_by(Order.total_amount.asc())
    else:  # newest
        query = query.order_by(Order.created_at.desc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page)
    orders = pagination.items
    
    return render_template('user/orders.html', 
                         orders=orders,
                         pagination=pagination)

@user_bp.route('/order/<int:order_id>')
@login_required
@customer_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('user.orders'))
    return render_template('user/order_detail.html', order=order)

@user_bp.route('/track-order/<int:order_id>')
@login_required
@customer_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('user.orders'))
    return render_template('user/track_order.html', order=order)

@user_bp.route('/negotiations')
@login_required
def negotiations():
    # Get search and filter parameters
    search_query = request.args.get('q', '')
    status = request.args.get('status')
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Base query
    query = Negotiation.query.filter_by(customer_id=current_user.id)
    
    # Apply search filter
    if search_query:
        query = query.join(Negotiation.product).join(Product.shop).filter(
            or_(
                Product.name.ilike(f'%{search_query}%'),
                Shop.name.ilike(f'%{search_query}%')
            )
        )
    
    # Apply status filter
    if status:
        query = query.filter_by(status=status)
    
    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(Negotiation.created_at.asc())
    elif sort == 'highest_offer':
        query = query.order_by(Negotiation.offered_price.desc())
    elif sort == 'lowest_offer':
        query = query.order_by(Negotiation.offered_price.asc())
    else:  # newest
        query = query.order_by(Negotiation.created_at.desc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page)
    negotiations = pagination.items
    
    return render_template('user/negotiations.html',
                         negotiations=negotiations,
                         pagination=pagination)

@user_bp.route('/negotiation/<int:nego_id>')
@login_required
def negotiation_detail(nego_id):
    negotiation = Negotiation.query.get_or_404(nego_id)
    if negotiation.customer_id != current_user.id:
        flash('Access denied.', 'error')
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
    
    if negotiation.status not in ['pending', 'counter_offer']:
        return jsonify({
            'status': 'error',
            'message': 'This negotiation is no longer active'
        }), 400
    
    try:
        offered_price = float(request.json.get('offered_price'))
        if offered_price <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({
            'status': 'error',
            'message': 'Invalid offer amount'
        }), 400
    
    negotiation.offered_price = offered_price
    negotiation.rounds += 1
    
    # Process with negotiation bot
    decision, counter_offer, message = process_negotiation(negotiation)
    
    if decision == 'accept':
        negotiation.accept_offer(offered_price)
    elif decision == 'reject':
        negotiation.reject_offer()
    else:  # counter
        negotiation.add_counter_offer(counter_offer)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'decision': decision,
        'message': message,
        'counter_offer': counter_offer,
        'negotiation': negotiation.to_dict()
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
    
    # Get search and filter parameters
    search_query = request.args.get('q', '')
    max_distance = float(request.args.get('distance', '10'))  # Default 10km
    sort_by = request.args.get('sort', 'distance')
    selected_categories = request.args.getlist('categories[]')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Base query starting with active shops
    query = Shop.query.filter_by(is_active=True)
    
    # Apply search filter if provided
    if search_query:
        query = query.join(Shop.products).filter(
            or_(
                Shop.name.ilike(f'%{search_query}%'),
                Shop.description.ilike(f'%{search_query}%'),
                Product.name.ilike(f'%{search_query}%'),
                Product.category.ilike(f'%{search_query}%')
            )
        ).distinct()
    
    # Filter by categories if selected
    if selected_categories:
        query = query.join(Shop.products).filter(
            Product.category.in_(selected_categories)
        ).distinct()
    
    # Add distance calculation
    query = query.add_columns(
        func.round(
            func.acos(
                func.sin(func.radians(current_user.location_lat)) * 
                func.sin(func.radians(Shop.location_lat)) +
                func.cos(func.radians(current_user.location_lat)) * 
                func.cos(func.radians(Shop.location_lat)) * 
                func.cos(func.radians(Shop.location_lng) - 
                        func.radians(current_user.location_lng))
            ) * 6371,  # Earth's radius in kilometers
            2
        ).label('distance')
    )
    
    # Filter by maximum distance
    query = query.having(func.coalesce('distance', float('inf')) <= max_distance)
    
    # Apply sorting
    if sort_by == 'rating':
        query = query.order_by(Shop.rating.desc(), 'distance')
    elif sort_by == 'products':
        query = query.outerjoin(Shop.products)\
                    .group_by(Shop.id)\
                    .order_by(func.count(Product.id).desc(), 'distance')
    else:  # distance
        query = query.order_by('distance')
    
    # Execute query with pagination
    pagination = query.paginate(page=page, per_page=per_page)
    shops_with_distance = pagination.items
    
    # Prepare shops list with distance
    shops = []
    for shop, distance in shops_with_distance:
        shop.distance = distance
        shops.append(shop)
    
    # Get unique categories from all products for the filter
    categories = db.session.query(Product.category)\
        .distinct()\
        .filter(Product.category.isnot(None))\
        .order_by(Product.category)\
        .all()
    categories = [c[0] for c in categories]
    
    return render_template('user/nearby_shops.html',
                         shops=shops,
                         categories=categories,
                         selected_categories=selected_categories,
                         pagination=pagination)

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