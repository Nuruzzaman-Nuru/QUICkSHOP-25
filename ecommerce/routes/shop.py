from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, or_, desc, asc, String
from functools import wraps
from werkzeug.utils import secure_filename
import os
from ..models.shop import Shop, Product
from ..models.user import User
from ..models.order import Order
from ..utils.notifications import notify_customer_order_status
from .. import db

shop_bp = Blueprint('shop', __name__, url_prefix='/shop')

def shop_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_shop_owner:
            flash('Access denied. Shop owner privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def owner_required(shop_id):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            shop = Shop.query.get_or_404(shop_id)
            if shop.owner_id != current_user.id:
                flash('Access denied. You do not own this shop.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@shop_bp.route('/')
def index():
    shops = Shop.query.filter_by(is_active=True).all()
    return render_template('shop/index.html', shops=shops)

@shop_bp.route('/<int:shop_id>')
def view(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    return render_template('shop/view.html', shop=shop)

@shop_bp.route('/dashboard')
@login_required
@shop_owner_required
def dashboard():
    shop = current_user.shop
    if not shop:
        return redirect(url_for('shop.create'))
    
    # Get statistics
    products_count = len(shop.products)
    active_orders = Order.query.filter(
        Order.shop_id == shop.id,
        Order.status.in_(['pending', 'confirmed', 'delivering'])
    ).all()
    active_orders_count = len(active_orders)
    
    # Calculate total revenue
    total_revenue = db.session.query(func.sum(Order.total_amount))\
        .filter(Order.shop_id == shop.id,
                Order.status == 'completed')\
        .scalar() or 0.0
    
    # Get recent orders
    recent_orders = Order.query.filter_by(shop_id=shop.id)\
        .order_by(Order.created_at.desc())\
        .limit(5).all()
    
    # Get low stock products (less than 10 items)
    low_stock_products = [p for p in shop.products if p.stock < 10]
    
    return render_template('shop/dashboard.html',
                         shop=shop,
                         products_count=products_count,
                         active_orders_count=active_orders_count,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products)

@shop_bp.route('/create', methods=['GET', 'POST'])
@login_required
@shop_owner_required
def create():
    if current_user.shop:
        flash('You already have a shop.', 'info')
        return redirect(url_for('shop.dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        address = request.form.get('address')
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        
        if not all([name, description, address]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('shop.create'))
            
        try:
            shop = Shop(
                name=name,
                description=description,
                address=address,
                location_lat=float(lat) if lat else None,
                location_lng=float(lng) if lng else None,
                owner_id=current_user.id
            )
            db.session.add(shop)
            db.session.commit()
            flash('Shop created successfully!', 'success')
            return redirect(url_for('shop.dashboard'))
        except ValueError:
            flash('Invalid coordinates provided.', 'error')
            
    return render_template('shop/create.html')

@shop_bp.route('/manage')
@login_required
@shop_owner_required
def manage():
    shop = current_user.shop
    if not shop:
        return redirect(url_for('shop.create'))
    return render_template('shop/manage.html', shop=shop)

@shop_bp.route('/orders')
@login_required
@shop_owner_required
def orders():
    shop = current_user.shop
    if not shop:
        return redirect(url_for('shop.create'))
    
    # Get search and filter parameters
    search_query = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of orders per page
    
    # Base query
    query = Order.query.filter_by(shop_id=shop.id)
    
    # Apply search filter
    if search_query:
        # Search by order ID or customer username
        try:
            order_id = int(search_query)
            query = query.filter(Order.id == order_id)
        except ValueError:
            query = query.join(Order.customer).filter(
                or_(
                    User.username.ilike(f'%{search_query}%'),
                    User.email.ilike(f'%{search_query}%')
                )
            )
    
    # Apply status filter
    if status:
        query = query.filter(Order.status == status)
    
    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(Order.created_at.asc())
    elif sort == 'highest':
        query = query.order_by(Order.total_amount.desc())
    elif sort == 'lowest':
        query = query.order_by(Order.total_amount.asc())
    else:  # newest
        query = query.order_by(Order.created_at.desc())
    
    # Execute query with pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items
    
    # Get counts for different statuses for the status filter badges
    status_counts = {
        'all': query.count(),
        'pending': query.filter(Order.status == 'pending').count(),
        'confirmed': query.filter(Order.status == 'confirmed').count(),
        'delivering': query.filter(Order.status == 'delivering').count(),
        'completed': query.filter(Order.status == 'completed').count(),
        'cancelled': query.filter(Order.status == 'cancelled').count()
    }
    
    return render_template('shop/orders.html', 
                         orders=orders,
                         pagination=pagination,
                         status_counts=status_counts,
                         current_status=status,
                         current_sort=sort,
                         search_query=search_query)

@shop_bp.route('/order/<int:order_id>/details')
@login_required
@shop_owner_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    if order.shop_id != current_user.shop.id:
        flash('Access denied.', 'error')
        return redirect(url_for('shop.orders'))
    return render_template('shop/order_details.html', order=order)

@shop_bp.route('/order/<int:order_id>/update-status', methods=['POST'])
@login_required
@shop_owner_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Verify shop owner owns this order
    if order.shop_id != current_user.shop.id:
        return jsonify({
            'status': 'error',
            'message': 'Access denied. This order belongs to another shop.'
        }), 403
    
    data = request.get_json()
    new_status = data.get('status')
    
    try:
        if order.update_status(new_status):
            db.session.commit()
            # Send notifications
            notify_customer_order_status(order)
            notify_admin_order_status(order)
            
            if new_status == 'confirmed':
                # Notify available delivery personnel
                notify_delivery_person_new_order(order)
            
            return jsonify({
                'status': 'success',
                'message': f'Order status updated to {new_status}'
            })
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating order status'
        }), 500

@shop_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@shop_owner_required
def settings():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Update username and email
        if username and email:
            current_user.username = username
            current_user.email = email
            
        # Update password if provided
        if current_password and new_password and confirm_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('shop.settings'))
                
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('shop.settings'))
                
            current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating settings.', 'error')
            
    return render_template('shop/settings.html')

@shop_bp.route('/analytics')
@login_required
@shop_owner_required
def analytics():
    shop = current_user.shop
    if not shop:
        return redirect(url_for('shop.create'))
    return render_template('shop/analytics.html', shop=shop)

@shop_bp.route('/inventory')
@login_required
@shop_owner_required
def inventory():
    shop = current_user.shop
    if not shop:
        return redirect(url_for('shop.create'))
    return render_template('shop/inventory.html', shop=shop)

@shop_bp.route('/negotiation-settings', methods=['GET', 'POST'])
@login_required
@shop_owner_required
def negotiation_settings():
    shop = current_user.shop
    if not shop:
        return redirect(url_for('shop.create'))
        
    if request.method == 'POST':
        # Handle negotiation settings update
        pass
        
    return render_template('shop/negotiation_settings.html', shop=shop)

@shop_bp.route('/<int:shop_id>/update', methods=['POST'])
@login_required
@shop_owner_required
def update_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'You can only update your own shop'
        }), 403
    
    try:
        shop.name = request.form.get('name')
        shop.description = request.form.get('description')
        shop.address = request.form.get('address')
        shop.location_lat = float(request.form.get('latitude'))
        shop.location_lng = float(request.form.get('longitude'))
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Shop updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@shop_bp.route('/<int:shop_id>/products/add', methods=['GET', 'POST'])
@login_required
@shop_owner_required
def add_product(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('shop.index'))
    
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form.get('name'),
                description=request.form.get('description'),
                price=float(request.form.get('price')),
                stock=int(request.form.get('stock')),
                shop_id=shop_id
            )
            
            # Handle negotiation settings
            if request.form.get('min_price'):
                product.min_price = float(request.form.get('min_price'))
                product.max_discount_percentage = float(request.form.get('max_discount', 20))
            
            db.session.add(product)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Product added successfully'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        
    return render_template('shop/add_product.html', shop=shop)

@shop_bp.route('/product/<int:product_id>/update', methods=['POST'])
@login_required
@shop_owner_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.shop.owner_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'You can only update products in your own shop'
        }), 403
    
    try:
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        
        if request.form.get('min_price'):
            product.min_price = float(request.form.get('min_price'))
            product.max_discount_percentage = float(request.form.get('max_discount', 20))
        else:
            product.min_price = None
            product.max_discount_percentage = None
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Product updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@shop_bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
@shop_owner_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.shop.owner_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'You can only delete products from your own shop'
        }), 403
    
    try:
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Product deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@shop_bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@shop_owner_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Ensure the product belongs to the current user's shop
    if product.shop.owner_id != current_user.id:
        flash('Access denied. You do not own this product.', 'error')
        return redirect(url_for('shop.dashboard'))
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price', 0))
        product.stock = int(request.form.get('stock', 0))
        product.category = request.form.get('category')
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                product.image = filename
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('shop.dashboard'))
    
    return render_template('shop/edit_product.html', product=product)

@shop_bp.route('/product/<int:product_id>/update-negotiation', methods=['POST'])
@login_required
@shop_owner_required
def update_negotiation_settings(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Ensure the product belongs to the current user's shop
    if product.shop.owner_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'Access denied. You do not own this product.'
        }), 403
        
    try:
        min_price = request.form.get('min_price', '').strip()
        max_discount = float(request.form.get('max_discount', 20))
        
        # Set min_price to None if empty (disables negotiation)
        product.min_price = float(min_price) if min_price else None
        product.max_discount_percentage = max(0, min(max_discount, 100))  # Clamp between 0-100
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Negotiation settings updated successfully'
        })
        
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid value provided for price or discount'
        }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500