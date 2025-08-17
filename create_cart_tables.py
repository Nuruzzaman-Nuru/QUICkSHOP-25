from ecommerce import create_app, db
from ecommerce.models.cart import Cart, CartItem

app = create_app()

with app.app_context():
    # Create the tables
    db.session.execute('DROP TABLE IF EXISTS cart_item')
    db.session.execute('DROP TABLE IF EXISTS cart')
    
    db.session.execute('''
    CREATE TABLE cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    ''')
    
    db.session.execute('''
    CREATE TABLE cart_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        negotiated_price FLOAT,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(cart_id) REFERENCES cart(id),
        FOREIGN KEY(product_id) REFERENCES product(id)
    )
    ''')
    
    db.session.commit()
    print("Cart tables created successfully!")
