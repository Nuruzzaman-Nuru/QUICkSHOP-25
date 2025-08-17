from flask import Blueprint, render_template, session, flash, redirect, url_for, request, current_app, send_from_directory, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from ..models.shop import Shop, Product
from ..models.order import Order, OrderItem
from ..models.cart import Cart, CartItem
from ..routes.auth import customer_required
from ..routes.api import init_cart, get_or_create_cart
from ..utils.notifications import notify_shop_owner_new_order, notify_customer_order_status, notify_admin_order_status
from .. import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get active shops
    featured_shops = Shop.query.filter_by(is_active=True).limit(6).all()
    
    # Get featured products - products with high ratings or recent additions
    featured_products = Product.query.join(Shop)\
        .filter(Shop.is_active == True)\
        .order_by(Product.rating.desc(), Product.created_at.desc())\
        .limit(3).all()  # Limit to 3 products as shown in the static example
    
    return render_template('main/home.html', 
                         featured_shops=featured_shops,
                         featured_products=featured_products,
                         current_date="May 5, 2025")

@main_bp.route('/about')
def about():
    # Show default QuickShop about page for non-logged in users
    # or users that are not shop owners
    if not current_user.is_authenticated or current_user.role != 'shop_owner':
        return render_template('main/about.html')
    
    # Redirect shop owners to their shop's about page
    shop = Shop.query.filter_by(owner_id=current_user.id).first()
    if shop:
        return redirect(url_for('shop.about', shop_id=shop.id))
    return render_template('main/about.html')

@main_bp.route('/projects')
def projects():
    return render_template('main/projects.html')

@main_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
@customer_required
def checkout():
    cart = get_or_create_cart()
    if isinstance(cart, dict) and not cart:  # Empty session cart
        return render_template('main/checkout.html', cart_items=[])
    elif not isinstance(cart, dict) and not cart.items:  # Empty database cart
        return render_template('main/checkout.html', cart_items=[])

    if request.method == 'POST':
        # Get form data
        delivery_address = request.form.get('address', '').strip()
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        payment_method = request.form.get('payment_method', 'cod')
        notes = request.form.get('notes', '').strip()
        
        # Validate delivery address
        if not delivery_address:
            flash('Please provide a delivery address.', 'error')
            return redirect(url_for('main.checkout'))
            
        # Only validate coordinates if they are provided
        if latitude is not None and longitude is not None:
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                flash('Invalid coordinates provided. Please enter a valid address.', 'error')
                return redirect(url_for('main.checkout'))

        try:
            # Group items by shop
            shop_orders = {}
            
            # Handle database cart
            if not isinstance(cart, dict):
                for cart_item in cart.items:
                    product = cart_item.product
                    if not product:
                        continue
                        
                    if product.shop_id not in shop_orders:
                        shop_orders[product.shop_id] = []
                        
                    shop_orders[product.shop_id].append({
                        'product': product,
                        'quantity': cart_item.quantity,
                        'price': cart_item.negotiated_price or product.price
                    })
            # Handle session cart
            else:
                for product_id, item in cart.items():
                    product = Product.query.get(product_id)
                    if not product:
                        continue
                        
                    if product.shop_id not in shop_orders:
                        shop_orders[product.shop_id] = []
                        
                    shop_orders[product.shop_id].append({
                        'product': product,
                        'quantity': item['quantity'],
                        'price': item['price']
                    })

            # Create separate orders for each shop
            orders = []
            for shop_id, items in shop_orders.items():
                order = Order(
                    customer_id=current_user.id,
                    shop_id=shop_id,
                    status='pending',
                    payment_method=payment_method,
                    special_instructions=notes
                )

                # Set delivery address if provided
                if delivery_address:
                    order.delivery_address = delivery_address
                    order.delivery_lat = latitude
                    order.delivery_lng = longitude

                # Add items to order and calculate total
                total_amount = 0
                for item in items:
                    order_item = OrderItem(
                        product_id=item['product'].id,
                        quantity=item['quantity'],
                        price=item['price'],
                        shop_id=shop_id
                    )
                    order.items.append(order_item)
                    total_amount += item['quantity'] * item['price']
                    
                    # Update product stock
                    item['product'].stock -= item['quantity']

                order.total_amount = total_amount
                db.session.add(order)
                orders.append(order)

            # Clear cart
            if not isinstance(cart, dict):
                for item in cart.items:
                    db.session.delete(item)
            else:
                session['cart'] = {}

            db.session.commit()

            # Send notifications
            for order in orders:
                notify_shop_owner_new_order(order)
                notify_customer_order_status(order)
                notify_admin_order_status(order, {
                    'old': None,
                    'new': 'pending',
                    'action': 'order_created'
                })

            flash('Orders placed successfully!', 'success')
            # Redirect to the first order if multiple orders were created
            return redirect(url_for('user.order_detail', order_id=orders[0].id))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')
            return redirect(url_for('main.checkout'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while placing your order. Please try again. If the problem persists, contact support.', 'error')
            print(f'Error placing order: {str(e)}')  # Log the actual error
            return redirect(url_for('main.checkout'))

    # GET request - show checkout form
    cart_items = []
    total = 0
    
    # Handle database cart
    if not isinstance(cart, dict):
        for cart_item in cart.items:
            product = cart_item.product
            if product:
                price = cart_item.negotiated_price or product.price
                subtotal = price * cart_item.quantity
                cart_items.append({
                    'product': product,
                    'quantity': cart_item.quantity,
                    'price': price,
                    'subtotal': subtotal
                })
                total += subtotal
    # Handle session cart
    else:
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
@customer_required
def cart():
    cart = get_or_create_cart()
    cart_items = []
    total = 0
    
    # Handle database cart
    if not isinstance(cart, dict):
        for cart_item in cart.items:
            product = cart_item.product
            if product:
                price = cart_item.negotiated_price or product.price
                subtotal = price * cart_item.quantity
                cart_items.append({
                    'product': product,
                    'quantity': cart_item.quantity,
                    'price': price,
                    'subtotal': subtotal,
                    'negotiated': cart_item.negotiated_price is not None
                })
                total += subtotal
    # Handle session cart
    else:
        for product_id, item in cart.items():
            product = Product.query.get(product_id)
            if product:
                subtotal = item['quantity'] * item['price']
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'subtotal': subtotal,
                    'negotiated': False
                })
                total += subtotal
    
    return render_template('main/cart.html', cart_items=cart_items, total=total)

@main_bp.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)

@main_bp.route('/search')
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    shop_id = request.args.get('shop_id', type=int)
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort = request.args.get('sort', 'relevance')
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of items per page

    # Location-based search parameters
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    distance = request.args.get('distance', 10, type=float)  # Default 10km radius

    # Initialize queries
    product_query = Product.query.filter(Product.shop.has(Shop.is_active == True))
    shop_query = Shop.query.filter_by(is_active=True)

    # Apply location filter if coordinates are provided
    if lat is not None and lng is not None:
        # Haversine formula for distance calculation in kilometers
        distance_formula = (
            6371 * func.acos(
                func.sin(func.radians(lat)) * 
                func.sin(func.radians(Shop.location_lat)) +
                func.cos(func.radians(lat)) * 
                func.cos(func.radians(Shop.location_lat)) * 
                func.cos(func.radians(Shop.location_lng) - func.radians(lng))
            )
        )
        
        shop_query = shop_query.add_columns(
            distance_formula.label('distance')
        ).having(distance_formula <= distance)
        
        if search_type in ['all', 'products']:
            product_query = product_query.join(Shop).add_columns(
                distance_formula.label('distance')
            ).having(distance_formula <= distance)

    # Apply shop filter if specified
    if shop_id:
        shop = Shop.query.get_or_404(shop_id)
        product_query = product_query.filter(Product.shop_id == shop_id)
        search_type = 'products'

    # Apply text search filters
    if query:
        if search_type in ['all', 'products']:
            product_query = product_query.filter(
                or_(
                    Product.name.ilike(f'%{query}%'),
                    Product.description.ilike(f'%{query}%'),
                    Product.category.ilike(f'%{query}%')
                )
            )
        
        if search_type in ['all', 'shops'] and not shop_id:
            shop_query = shop_query.filter(
                or_(
                    Shop.name.ilike(f'%{query}%'),
                    Shop.description.ilike(f'%{query}%'),
                    Shop.address.ilike(f'%{query}%')
                )
            )

    # Apply product filters
    if search_type != 'shops':
        if category:
            product_query = product_query.filter(Product.category == category)
        
        if min_price is not None:
            product_query = product_query.filter(Product.price >= min_price)
        if max_price is not None:
            product_query = product_query.filter(Product.price <= max_price)
        
        # Sorting products
        if sort == 'price_low':
            product_query = product_query.order_by(Product.price.asc())
        elif sort == 'price_high':
            product_query = product_query.order_by(Product.price.desc())
        elif sort == 'newest':
            product_query = product_query.order_by(Product.created_at.desc())
        else:  # relevance
            if query:
                from sqlalchemy import text
                product_query = product_query.order_by(text("(CASE "
                    "WHEN name LIKE :query THEN 3 "
                    "WHEN category LIKE :query THEN 2 "
                    "WHEN description LIKE :query THEN 1 "
                    "ELSE 0 END) DESC").bindparams(query=f"%{query}%"))

    # Sort shops by distance if location provided
    if lat is not None and lng is not None:
        shop_query = shop_query.order_by('distance')

    # Execute queries with pagination
    products_pagination = product_query.paginate(page=page, per_page=per_page) if search_type != 'shops' else None
    shops_pagination = shop_query.paginate(page=page, per_page=per_page) if search_type != 'products' and not shop_id else None

    # Get unique categories for filter options
    categories = db.session.query(Product.category)\
                         .distinct()\
                         .filter(Product.category != None)\
                         .order_by(Product.category)\
                         .all()
    categories = [cat[0] for cat in categories]

    return render_template('main/search_results.html',
                         products=products_pagination.items if products_pagination else [],
                         shops=shops_pagination.items if shops_pagination else [],
                         products_pagination=products_pagination,
                         shops_pagination=shops_pagination,
                         query=query,
                         search_type=search_type,
                         current_category=category,
                         categories=categories,
                         min_price=min_price,
                         max_price=max_price,
                         current_sort=sort,
                         shop=Shop.query.get(shop_id) if shop_id else None,
                         search_lat=lat,
                         search_lng=lng,
                         search_distance=distance,
                         config={'GOOGLE_MAPS_API_KEY': current_app.config['GOOGLE_MAPS_API_KEY']})

@main_bp.route('/contact', methods=['GET'])
def contact_page():
    return render_template('main/contact.html')

@main_bp.route('/contact', methods=['POST'])
def contact_submit():
    data = request.get_json()
    # Here you would typically send an email or save to database
    # For now, we'll just return a success response
    return jsonify({
        'status': 'success',
        'message': 'Thank you for your message. We will get back to you soon!'
    })

@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500