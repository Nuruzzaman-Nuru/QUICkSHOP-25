from ecommerce import create_app, db
from ecommerce.models.cart import Cart, CartItem
from sqlalchemy import text

def reset_cart_tables():
    app = create_app()
    with app.app_context():
        try:
            # Drop existing tables if they exist
            db.session.execute(text('DROP TABLE IF EXISTS cart_item'))
            db.session.execute(text('DROP TABLE IF EXISTS cart'))
            db.session.commit()
            print("Dropped existing cart tables")
            
            # Create cart table
            db.session.execute(text('''
                CREATE TABLE cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES user(id)
                )
            '''))
            
            # Create cart_item table
            db.session.execute(text('''
                CREATE TABLE cart_item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cart_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    negotiated_price FLOAT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(cart_id) REFERENCES cart(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES product(id)
                )
            '''))
            
            db.session.commit()
            print("Created new cart tables successfully!")
            
            # Verify the tables were created
            inspector = db.inspect(db.engine)
            print("\nVerifying tables structure:")
            
            print("\nCart table columns:")
            for column in inspector.get_columns('cart'):
                print(f"- {column['name']}: {column['type']}")
                
            print("\nCartItem table columns:")
            for column in inspector.get_columns('cart_item'):
                print(f"- {column['name']}: {column['type']}")
                
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    reset_cart_tables()
