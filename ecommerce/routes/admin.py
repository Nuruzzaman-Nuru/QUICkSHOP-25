from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from functools import wraps
from ..models.user import User
from ..models.shop import Shop
from ..models.order import Order
from ..utils.notifications import (
    notify_all_delivery_persons,
    notify_admin_order_status,
    notify_delivery_assignment,
    notify_customer_order_status
)
from .. import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    shops_count = Shop.query.count()
    active_orders_count = Order.query.filter(
        Order.status.in_(['pending', 'confirmed', 'delivering'])
    ).count()
    delivery_count = User.query.filter_by(role='delivery').count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(
        Order.created_at.desc()
    ).limit(5).all()
    
    # Get delivery assignments
    delivery_assignments = Order.query.filter(
        Order.status.in_(['confirmed', 'pending'])
    ).order_by(Order.created_at.asc()).limit(5).all()
    
    # Get all users for notification system
    users = User.query.all()
    
    return render_template('admin/dashboard.html',
                         shops_count=shops_count,
                         active_orders_count=active_orders_count,
                         delivery_count=delivery_count,
                         recent_orders=recent_orders,
                         delivery_assignments=delivery_assignments,
                         users=users)

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    status = request.args.get('status', None)
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
        
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@admin_bp.route('/order/<int:order_id>/details')
@login_required
@admin_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    available_delivery = User.query.filter_by(role='delivery', is_active=True).all()
    return render_template('admin/order_details.html', 
                         order=order,
                         available_delivery=available_delivery)

@admin_bp.route('/order/<int:order_id>/assign-delivery', methods=['POST'])
@login_required
@admin_required
def assign_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    delivery_id = request.form.get('delivery_id')
    
    if not delivery_id:
        return jsonify({'success': False, 'error': 'No delivery person selected'}), 400
        
    delivery_person = User.query.get_or_404(delivery_id)
    if delivery_person.role != 'delivery':
        return jsonify({'success': False, 'error': 'Invalid delivery person'}), 400
        
    order.delivery_person_id = delivery_id
    order.status = 'delivering'
    db.session.commit()
    
    # Send notifications
    notify_delivery_assignment(order, delivery_person)
    notify_customer_order_status(order)
    
    return jsonify({'success': True})

@admin_bp.route('/manage-delivery')
@login_required
@admin_required
def manage_delivery():
    delivery_persons = User.query.filter_by(role='delivery').all()
    return render_template('admin/manage_delivery.html', 
                         delivery_persons=delivery_persons)

@admin_bp.route('/manage-shops')
@login_required
@admin_required
def manage_shops():
    shops = Shop.query.all()
    return render_template('admin/manage_shops.html', shops=shops)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        # Handle system settings updates
        pass
    return render_template('admin/settings.html')

@admin_bp.route('/send-notification', methods=['POST'])
@login_required
@admin_required
def send_notification():
    recipient_type = request.form.get('recipient_type')
    message = request.form.get('message')
    
    if not message:
        flash('Message is required', 'error')
        return redirect(url_for('admin.dashboard'))
        
    if recipient_type == 'all_delivery':
        notify_all_delivery_persons(message)
    elif recipient_type == 'all_shops':
        # Implement shop notification
        shops = Shop.query.all()
        for shop in shops:
            if shop.owner:
                # Implement shop owner notification
                pass
    elif recipient_type == 'specific_user':
        user_id = request.form.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                # Implement specific user notification
                pass
                
    flash('Notification sent successfully', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/track-delivery/<int:order_id>')
@login_required
@admin_required
def track_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/track_delivery.html', order=order)