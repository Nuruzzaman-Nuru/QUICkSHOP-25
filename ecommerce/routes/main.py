from flask import Blueprint, render_template, session, send_from_directory, request, redirect, url_for
from flask_login import login_required
from sqlalchemy import or_, func, and_
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

@main_bp.route('/search')
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    shop_id = request.args.get('shop_id', type=int)
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort = request.args.get('sort', 'relevance')
    
    if not any([query, category, min_price, max_price, shop_id]):
        return redirect(url_for('main.index'))
    
    # Product search
    product_query = Product.query.filter(Product.shop.has(Shop.is_active == True))
    shop_query = Shop.query.filter_by(is_active=True)

    # Apply shop filter if specified
    if shop_id:
        shop = Shop.query.get_or_404(shop_id)
        product_query = product_query.filter(Product.shop_id == shop_id)
        search_type = 'products'  # Force products-only search for shop-specific searches
    
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
                product_query = product_query.order_by(
                    func.case(
                        (Product.name.ilike(f'%{query}%'), 0),
                        (Product.category.ilike(f'%{query}%'), 1),
                        (Product.description.ilike(f'%{query}%'), 2),
                        else_=3
                    )
                )
    
    products = product_query.all() if search_type != 'shops' else []
    shops = shop_query.all() if search_type != 'products' and not shop_id else []
    
    # Get unique categories for filter options
    categories = db.session.query(Product.category).distinct().filter(Product.category != None).all()
    categories = [cat[0] for cat in categories]
    
    return render_template('main/search_results.html', 
                         products=products,
                         shops=shops,
                         query=query,
                         search_type=search_type,
                         current_category=category,
                         categories=categories,
                         min_price=min_price,
                         max_price=max_price,
                         current_sort=sort,
                         shop=Shop.query.get(shop_id) if shop_id else None)

@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500