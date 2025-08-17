from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import func, or_
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
from ..utils.sms import send_sms
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
def dashboard():    # Calculate dashboard statistics
    stats = {
        'total_users': User.query.filter_by(role='user').count(),
        'active_shops': Shop.query.filter_by(is_active=True).count(),
        'total_delivery': User.query.filter_by(role='delivery').count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'daily_revenue': Order.query.filter(
            Order.status == 'completed',
            func.date(Order.created_at) == func.date(func.now())
        ).with_entities(func.sum(Order.total_amount)).scalar() or 0,
        'recent_orders': Order.query.order_by(Order.created_at.desc()).limit(5).all(),
        'latest_shops': Shop.query.order_by(Shop.created_at.desc()).limit(5).all()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    status = request.args.get('status', None)
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
        
    orders = query.order_by(Order.created_at.desc()).all()
    
    # Define status color mapping for Bootstrap badges
    order_status_colors = {
        'pending': 'warning',
        'confirmed': 'info',
        'delivering': 'primary',
        'completed': 'success',
        'cancelled': 'danger'
    }
    
    return render_template('admin/orders.html', 
                         orders=orders,
                         order_status_colors=order_status_colors)

@admin_bp.route('/order/<int:order_id>/details')
@login_required
@admin_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    available_delivery = User.query.filter_by(role='delivery', is_active=True).all()
    
    # Define status color mapping for Bootstrap badges
    order_status_colors = {
        'pending': 'warning',
        'confirmed': 'info',
        'delivering': 'primary',
        'completed': 'success',
        'cancelled': 'danger'
    }
    
    return render_template('admin/order_details.html', 
                         order=order,
                         available_delivery=available_delivery,
                         order_status_colors=order_status_colors)

@admin_bp.route('/order/<int:order_id>/assign-delivery', methods=['POST'])
@login_required
@admin_required
def assign_delivery(order_id):
    if request.headers.get('X-CSRF-TOKEN') != generate_csrf():
        return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
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

@admin_bp.route('/order/<int:order_id>/confirm', methods=['POST'])
@login_required
@admin_required
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'pending':
        return jsonify({
            'status': 'error',
            'message': 'Order is not in pending status'
        }), 400
        
    try:
        # Update order status to confirmed
        order.status = 'confirmed'
        db.session.commit()
        
        # Send SMS to customer if phone number is available
        if order.customer.phone:
            message = f"Dear {order.customer.username}, your order #{order.id} has been confirmed. Thank you for shopping with us."
            sms_sent = send_sms(order.customer.phone, message)
        else:
            sms_sent = False
            
        # Send email notification regardless of SMS status
        notify_customer_order_status(order)
        
        return jsonify({
            'status': 'success',
            'message': 'Order confirmed successfully',
            'sms_sent': sms_sent
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/order/<int:order_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    notes = request.form.get('notes')
    
    if not status:
        flash('Please select a status', 'error')
        return redirect(url_for('admin.order_details', order_id=order.id))

    try:
        # Update order status with validation
        order.update_status(status)
        if notes:
            order.notes = notes

        # Send notifications
        notify_admin_order_status(order)
        notify_customer_order_status(order)
        
        # If order is confirmed, notify delivery persons
        if status == 'confirmed':
            notify_all_delivery_persons(order)
        
        db.session.commit()
        flash('Order status updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating order status: {str(e)}')
        flash('Error updating order status', 'error')

    return redirect(url_for('admin.order_details', order_id=order.id))

@admin_bp.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    try:
        # Update order status with validation
        order.update_status('cancelled')
        db.session.commit()
        
        # Send notifications
        notify_customer_order_status(order)
        notify_admin_order_status(order, {
            'old': 'pending',
            'new': 'cancelled',
            'action': 'order_cancelled'
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Order cancelled successfully'
        })
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while cancelling the order'
        }), 500

@admin_bp.route('/manage-delivery')
@login_required
@admin_required
def manage_delivery():
    # Get search and filter parameters
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status')
    
    # Base query
    query = User.query.filter_by(role='delivery')
    
    # Apply search filter
    if search_query:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                User.phone.ilike(f'%{search_query}%')
            )
        )
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    delivery_persons = query.order_by(User.created_at.desc()).all()
    return render_template('admin/manage_delivery.html', 
                         delivery_persons=delivery_persons)

@admin_bp.route('/delivery/<int:user_id>/details')
@login_required
@admin_required
def delivery_details(user_id):
    delivery_person = User.query.filter_by(id=user_id, role='delivery').first_or_404()
    
    # Define status color mapping for Bootstrap badges
    order_status_colors = {
        'pending': 'warning',
        'confirmed': 'info',
        'delivering': 'primary',
        'completed': 'success',
        'cancelled': 'danger'
    }
    
    return render_template('admin/delivery_details.html', 
                         delivery_person=delivery_person,
                         order_status_colors=order_status_colors)

@admin_bp.route('/api/admin/delivery/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_delivery_status(user_id):
    if request.headers.get('X-CSRFToken') != generate_csrf():
        return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
    delivery_person = User.query.filter_by(id=user_id, role='delivery').first_or_404()
    delivery_person.is_active = not delivery_person.is_active
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Delivery person {delivery_person.username} has been {"activated" if delivery_person.is_active else "deactivated"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/manage-shops')
@login_required
@admin_required
def manage_shops():
    # Get search and filter parameters
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status')
    
    # Base query
    query = Shop.query
    
    # Apply search filter
    if search_query:
        query = query.filter(
            or_(
                Shop.name.ilike(f'%{search_query}%'),
                Shop.location.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%')
            )
        ).join(User, Shop.owner_id == User.id, isouter=True)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    shops = query.order_by(Shop.created_at.desc()).all()
    return render_template('admin/manage_shops.html', shops=shops)

@admin_bp.route('/api/admin/shops/<int:shop_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_shop_status(shop_id):
    # Get CSRF token from header
    csrf_token = request.headers.get('X-CSRFToken')
    if not csrf_token:
        current_app.logger.error('CSRF token missing in request')
        return jsonify({'success': False, 'error': 'CSRF token missing'}), 403

    # Validate token
    try:
        if csrf_token != generate_csrf():
            current_app.logger.error('Invalid CSRF token')
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
    except Exception as e:
        current_app.logger.error(f'Error validating CSRF token: {str(e)}')
        return jsonify({'success': False, 'error': 'Error validating CSRF token'}), 403
        
    # Get and validate shop
    shop = Shop.query.get_or_404(shop_id)
    if not shop:
        return jsonify({'success': False, 'error': 'Shop not found'}), 404
        
    # Toggle status
    shop.is_active = not shop.is_active
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Shop {shop.name} has been {"activated" if shop.is_active else "deactivated"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        # Handle system settings updates
        pass
    return render_template('admin/settings.html')

@admin_bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    q = request.args.get('q', '').strip()
    role = request.args.get('role', 'user')
    
    # Query users with role filter
    query = User.query.filter_by(role=role)
    
    # Apply search filter if provided
    if q:
        search = f"%{q}%"
        query = query.filter(or_(
            User.username.ilike(search),
            User.email.ilike(search),
            User.address.ilike(search)
        ))
    
    users = query.order_by(User.id.desc()).all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Only allow managing regular users
    if user.role != 'user':
        return jsonify({'success': False, 'error': 'Cannot modify non-user accounts'}), 400
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'User {user.username} has been {"activated" if user.is_active else "deactivated"}'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling user status: {str(e)}')
        return jsonify({'success': False, 'error': 'Error updating user status'}), 500